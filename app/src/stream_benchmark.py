#!/usr/bin/env python3
"""
Main runner: stream_benchmark.py

Usage example:
python src/stream_benchmark.py --provider deepgram --api_key "..." --url "PODCAST_URL" --start 450 --duration 300 --segment_seconds 6 --reference_csv data/reference_segments.csv
"""

import argparse
import asyncio
import csv
import json
import time
from pathlib import Path
from typing import Optional

from app.src.audio_reader import run_ffmpeg_stream, pcm_chunks_from_stdout
from app.src.deepgram_ws import connect as deepgram_connect, send_audio as deepgram_send, close as deepgram_close
from app.src.assemblyai_ws import connect as assembly_connect, start_stream as assembly_start, send_audio as assembly_send, stop_stream as assembly_stop
from app.src.diarization_parser import parse_deepgram_event, parse_assemblyai_event
from app.src.metrics import compute_wer
from app.src.utils import iso_now

# Config
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes
# chunk ms for sending - smaller => lower latency but more messages
CHUNK_MS = 320
CHUNK_BYTES = int(SAMPLE_RATE * (CHUNK_MS/1000.0) * SAMPLE_WIDTH * CHANNELS)

TRANSCRIPTS_JSONL = "transcripts.jsonl"
METRICS_CSV = "data/sample_metrics_{provider}.csv"

class Runner:
    def __init__(self, provider: str, api_key: str, url: str, start: float, duration: float,
                 segment_seconds: float = 6.0, reference_csv: Optional[str]=None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.url = url
        self.start = start
        self.duration = duration
        self.segment_seconds = segment_seconds
        self.reference_csv = reference_csv
        self.metrics = []
        self.transcripts_f = open(TRANSCRIPTS_JSONL, "w", encoding="utf-8")
        # reference map segment_id -> reference_text
        self.reference_map = {}
        if reference_csv:
            try:
                with open(reference_csv, newline='', encoding='utf-8') as fh:
                    reader = csv.DictReader(fh)
                    for r in reader:
                        sid = int(r['segment_id'])
                        self.reference_map[sid] = r['reference_text']
            except FileNotFoundError:
                print("Reference CSV not found:", reference_csv)

    async def run(self):
        ff = run_ffmpeg_stream(self.url, self.start, self.duration, sample_rate=SAMPLE_RATE)
        print(f"[{iso_now()}] Started ffmpeg PID {ff.pid}")
        if self.provider == "deepgram":
            await self._run_deepgram(ff)
        elif self.provider == "assemblyai":
            await self._run_assemblyai(ff)
        else:
            raise ValueError("Unknown provider")
        ff.kill()
        self.transcripts_f.close()
        self._write_metrics()

    def _write_metrics(self):
        out = METRICS_CSV.format(provider=self.provider)
        Path("data").mkdir(parents=True, exist_ok=True)
        keys = ["provider_name","segment_id","start_timestamp_sec","final_text_timestamp_iso","latency_ms","hypothesis_text","reference_text","S","I","D","N"]
        with open(out, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            for r in self.metrics:
                writer.writerow(r)
        print(f"Wrote metrics to {out}")

    async def _run_deepgram(self, ff_proc):
        ws = await deepgram_connect(self.api_key, sample_rate=SAMPLE_RATE, diarize=True)
        print("Connected to Deepgram")
        # spawn listener
        listener = asyncio.create_task(self._deepgram_listener(ws))
        buffer = bytearray()
        seg_bytes = int(self.segment_seconds * SAMPLE_RATE * SAMPLE_WIDTH * CHANNELS)
        seg_start_audio_offset = self.start
        seg_id = 0
        try:
            for chunk in pcm_chunks_from_stdout(ff_proc, CHUNK_BYTES):
                await deepgram_send(ws, chunk)
                buffer += chunk
                if len(buffer) >= seg_bytes:
                    seg_id += 1
                    # record send time for this segment
                    t_send = time.time()
                    # store a row placeholder (complete when final arrives)
                    row = {
                        "provider_name": "Deepgram",
                        "segment_id": seg_id,
                        "start_timestamp_sec": round(seg_start_audio_offset,3),
                        "final_text_timestamp_iso": "",
                        "latency_ms": "",
                        "hypothesis_text": "",
                        "reference_text": self.reference_map.get(seg_id,""),
                        "S":"","I":"","D":"","N":""
                    }
                    # attach t_send for latency computation
                    row["_t_send"] = t_send
                    self.metrics.append(row)
                    seg_start_audio_offset += self.segment_seconds
                    buffer = bytearray()
                await asyncio.sleep(0)
            # send close message
            await deepgram_close(ws)
            await asyncio.sleep(2.0)
        finally:
            listener.cancel()
            try:
                await listener
            except Exception:
                pass

    async def _deepgram_listener(self, ws):
        # listen to events
        async for msg in ws:
            if isinstance(msg, bytes):
                continue
            try:
                j = json.loads(msg)
            except Exception:
                continue
            # write raw event
            self.transcripts_f.write(json.dumps({"provider":"deepgram","event":j,"iso":iso_now()}) + "\n")
            # try parsing diarized utterances
            utts = []
            try:
                utts = parse_deepgram_event(j)
            except Exception:
                pass
            if utts:
                # print diarized utterances
                for u in utts:
                    print(f"Speaker {u['speaker']}: {u['text']}")
                # find next metrics row without final_text set
                for row in reversed(self.metrics):
                    if row['final_text_timestamp_iso'] == "":
                        row['final_text_timestamp_iso'] = iso_now()
                        if "_t_send" in row:
                            try:
                                row['latency_ms'] = int((time.time() - row['_t_send'])*1000)
                            except Exception:
                                row['latency_ms'] = ""
                        row['hypothesis_text'] = " | ".join([f"Speaker {u['speaker']}: {u['text']}" for u in utts])
                        # compute WER if reference exists
                        ref = row.get('reference_text','')
                        if ref:
                            try:
                                S,I,D,N = compute_wer(ref, row['hypothesis_text'])
                                row['S'], row['I'], row['D'], row['N'] = S,I,D,N
                            except Exception:
                                pass
                        break

    async def _run_assemblyai(self, ff_proc):
        ws = await assembly_connect(self.api_key, sample_rate=SAMPLE_RATE)
        print("Connected to AssemblyAI")
        await assembly_start(ws)
        listener = asyncio.create_task(self._assembly_listener(ws))
        buffer = bytearray()
        seg_bytes = int(self.segment_seconds * SAMPLE_RATE * SAMPLE_WIDTH * CHANNELS)
        seg_start_audio_offset = self.start
        seg_id = 0
        try:
            for chunk in pcm_chunks_from_stdout(ff_proc, CHUNK_BYTES):
                await assembly_send(ws, chunk)
                buffer += chunk
                if len(buffer) >= seg_bytes:
                    seg_id += 1
                    t_send = time.time()
                    row = {
                        "provider_name": "AssemblyAI",
                        "segment_id": seg_id,
                        "start_timestamp_sec": round(seg_start_audio_offset,3),
                        "final_text_timestamp_iso": "",
                        "latency_ms": "",
                        "hypothesis_text": "",
                        "reference_text": self.reference_map.get(seg_id,""),
                        "S":"","I":"","D":"","N":""
                    }
                    row["_t_send"] = t_send
                    self.metrics.append(row)
                    seg_start_audio_offset += self.segment_seconds
                    buffer = bytearray()
                await asyncio.sleep(0)
            # stop stream
            await assembly_stop(ws)
            await asyncio.sleep(2.0)
        finally:
            listener.cancel()
            try:
                await listener
            except Exception:
                pass

    async def _assembly_listener(self, ws):
        async for msg in ws:
            if isinstance(msg, bytes):
                continue
            try:
                j = json.loads(msg)
            except Exception:
                continue
            # write raw event
            self.transcripts_f.write(json.dumps({"provider":"assemblyai","event":j,"iso":iso_now()}) + "\n")
            # parse utterances
            utts = []
            try:
                utts = parse_assemblyai_event(j)
            except Exception:
                pass
            if utts:
                for u in utts:
                    print(f"Speaker {u['speaker']}: {u['text']}")
                for row in reversed(self.metrics):
                    if row['final_text_timestamp_iso'] == "":
                        row['final_text_timestamp_iso'] = iso_now()
                        try:
                            row['latency_ms'] = int((time.time() - row['_t_send'])*1000)
                        except Exception:
                            row['latency_ms'] = ""
                        # join utterances texts
                        row['hypothesis_text'] = " | ".join([f"Speaker {u['speaker']}: {u['text']}" for u in utts])
                        ref = row.get('reference_text','')
                        if ref:
                            try:
                                S,I,D,N = compute_wer(ref, row['hypothesis_text'])
                                row['S'], row['I'], row['D'], row['N'] = S,I,D,N
                            except Exception:
                                pass
                        break

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True, choices=["deepgram","assemblyai"])
    p.add_argument("--api_key", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--duration", type=float, default=300.0)
    p.add_argument("--segment_seconds", type=float, default=6.0)
    p.add_argument("--reference_csv", default=None)
    return p.parse_args()

async def main():
    args = parse_args()
    runner = Runner(provider=args.provider, api_key=args.api_key, url=args.url,
                    start=args.start, duration=args.duration, segment_seconds=args.segment_seconds,
                    reference_csv=args.reference_csv)
    await runner.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted")
