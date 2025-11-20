# app/main.py
#!/usr/bin/env python3
"""
main.py — Real-time ASR Benchmark (NO FFMPEG VERSION)
"""

import asyncio
import csv
import json
import time
from pathlib import Path

from settings.constant import (
    DEFAULT_PROVIDER,
    DEEPGRAM_API_KEY,
    ASSEMBLYAI_API_KEY,
    PODCAST_URL,
    START_SEC,
    DURATION_SEC,
    SEGMENT_SECONDS,
    REFERENCE_CSV
)

from src.audio_reader import stream_audio_from_url
from src.deepgram_ws import connect as dg_connect, send_audio as dg_send, close as dg_close
from src.assemblyai_ws import connect as aa_connect, start_stream as aa_start, send_audio as aa_send, stop_stream as aa_stop
from src.diarization_parser import parse_deepgram_event, parse_assemblyai_event
from src.metrics import compute_wer
from src.utils import iso_now

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
CHUNK_MS = 320
CHUNK_BYTES = int(SAMPLE_RATE * (CHUNK_MS / 1000) * SAMPLE_WIDTH * CHANNELS)

TRANSCRIPT_LOG = "transcripts.jsonl"
CSV_TEMPLATE = "data/metrics_{provider}.csv"


class ASRBenchmark:

    def __init__(self, provider):
        self.provider = provider.lower()
        self.api_key = DEEPGRAM_API_KEY if self.provider == "deepgram" else ASSEMBLYAI_API_KEY

        self.url = PODCAST_URL
        self.segment_seconds = SEGMENT_SECONDS
        self.start = START_SEC
        self.duration = DURATION_SEC

        self.reference_map = self._load_reference(REFERENCE_CSV)
        self.metrics = []
        self.raw_log = open(TRANSCRIPT_LOG, "w", encoding="utf-8")

    def _load_reference(self, path):
        if not Path(path).exists():
            print(f"⚠ Reference CSV missing: {path}")
            return {}
        out = {}
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                out[int(row["segment_id"])] = row["reference_text"]
        print(f"Loaded {len(out)} reference segments.")
        return out

    async def run(self):
        print(f"\n🚀 Starting ASR Benchmark: {self.provider.upper()}")
        print(f"🎧 Streaming audio (NO FFMPEG): {self.url}")

        if self.provider == "deepgram":
            await self.run_deepgram()
        else:
            await self.run_assemblyai()

        self.raw_log.close()
        self._save_csv()

    async def run_deepgram(self):
        ws = await dg_connect(self.api_key)
        print("✔ Connected to Deepgram")

        listener = asyncio.create_task(self._listen_deepgram(ws))
        audio_stream = stream_audio_from_url(self.url, CHUNK_BYTES)

        seg_bytes = int(self.segment_seconds * SAMPLE_RATE * SAMPLE_WIDTH * CHANNELS)
        buffer = bytearray()
        seg_start = self.start
        seg_id = 0

        try:
            for chunk in audio_stream:
                await dg_send(ws, chunk)
                buffer += chunk
                if len(buffer) >= seg_bytes:
                    seg_id += 1
                    self._start_segment(seg_id, seg_start)
                    seg_start += self.segment_seconds
                    buffer = bytearray()
                await asyncio.sleep(0)
            await dg_close(ws)
            await asyncio.sleep(1)
        finally:
            listener.cancel()

    async def _listen_deepgram(self, ws):
        async for msg in ws:
            if isinstance(msg, bytes):
                continue
            event = json.loads(msg)
            self._log_raw("deepgram", event)
            utts = parse_deepgram_event(event)
            if utts:
                self._finalize_segment(utts)

    async def run_assemblyai(self):
        ws = await aa_connect(self.api_key)
        await aa_start(ws)
        print("✔ Connected to AssemblyAI")

        listener = asyncio.create_task(self._listen_assembly(ws))
        audio_stream = stream_audio_from_url(self.url, CHUNK_BYTES)

        seg_bytes = int(self.segment_seconds * SAMPLE_RATE * SAMPLE_WIDTH * CHANNELS)
        buffer = bytearray()
        seg_start = self.start
        seg_id = 0

        try:
            for chunk in audio_stream:
                await aa_send(ws, chunk)
                buffer += chunk
                if len(buffer) >= seg_bytes:
                    seg_id += 1
                    self._start_segment(seg_id, seg_start)
                    seg_start += self.segment_seconds
                    buffer = bytearray()
                await asyncio.sleep(0)
            await aa_stop(ws)
            await asyncio.sleep(1)
        finally:
            listener.cancel()

    async def _listen_assembly(self, ws):
        async for msg in ws:
            if isinstance(msg, bytes):
                continue
            event = json.loads(msg)
            self._log_raw("assemblyai", event)
            utts = parse_assemblyai_event(event)
            if utts:
                self._finalize_segment(utts)

    def _log_raw(self, provider, event):
        self.raw_log.write(json.dumps({
            "provider": provider,
            "event": event,
            "time": iso_now()
        }) + "\n")

    def _start_segment(self, seg_id, start_sec):
        row = {
            "provider_name": self.provider,
            "segment_id": seg_id,
            "start_timestamp_sec": start_sec,
            "final_text_timestamp_iso": "",
            "latency_ms": "",
            "hypothesis_text": "",
            "reference_text": self.reference_map.get(seg_id, ""),
            "_send_time": time.time(),
        }
        self.metrics.append(row)

    def _finalize_segment(self, utts):
        for u in utts:
            print(f"🗣 Speaker {u['speaker']}: {u['text']}")
        for row in reversed(self.metrics):
            if not row["final_text_timestamp_iso"]:
                row["final_text_timestamp_iso"] = iso_now()
                row["latency_ms"] = int((time.time() - row["_send_time"]) * 1000)
                row["hypothesis_text"] = " | ".join(
                    f"Speaker {u['speaker']}: {u['text']}" for u in utts
                )
                ref = row["reference_text"]
                if ref:
                    S, I, D, N = compute_wer(ref, row["hypothesis_text"])
                    row.update({"S": S, "I": I, "D": D, "N": N})
                break

    def _save_csv(self):
        filename = CSV_TEMPLATE.format(provider=self.provider)
        Path("data").mkdir(exist_ok=True)
        keys = [
            "provider_name", "segment_id", "start_timestamp_sec",
            "final_text_timestamp_iso", "latency_ms",
            "hypothesis_text", "reference_text", "S", "I", "D", "N"
        ]
        with open(filename, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for row in self.metrics:
                w.writerow({k: row.get(k, "") for k in keys})
        print(f"\n📄 Metrics saved: {filename}")


async def main():
    benchmark = ASRBenchmark(DEFAULT_PROVIDER)
    await benchmark.run()

if __name__ == "__main__":
    asyncio.run(main())
