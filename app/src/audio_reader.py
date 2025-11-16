"""
audio_reader.py

Small helper to spawn ffmpeg that reads a remote URL or local file and outputs PCM16LE to stdout.
"""

import subprocess

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes

def run_ffmpeg_stream(url: str, start_s: float, duration_s: float, sample_rate: int = SAMPLE_RATE) -> subprocess.Popen:
    args = [
        "ffmpeg",
        "-ss", str(start_s),
        "-i", url,
        "-t", str(duration_s),
        "-ar", str(sample_rate),
        "-ac", str(CHANNELS),
        "-f", "s16le",
        "-hide_banner",
        "-loglevel", "error",
        "pipe:1"
    ]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=0)
    return p

def pcm_chunks_from_stdout(proc: subprocess.Popen, chunk_bytes: int):
    assert proc.stdout is not None
    while True:
        data = proc.stdout.read(chunk_bytes)
        if not data:
            break
        yield data