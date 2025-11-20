"""
audio_reader.py
MP3 → PCM16 streaming decoder using ffmpeg-python.
Works on Windows with NO system installation of ffmpeg.
"""

import os
import subprocess
from ffmpeg_downloader import FFmpegDownloader

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM


def get_ffmpeg_path():
    """
    Returns the local ffmpeg.exe path installed by ffmpeg-downloader.
    """
    ff = FFmpegDownloader().binary_path
    if not os.path.isfile(ff):
        raise FileNotFoundError("FFmpeg binary not found. Run: ffmpeg-downloader")
    return ff


def stream_audio_from_url(url: str, chunk_bytes: int):
    """
    Real-time MP3 streaming:
    URL → ffmpeg (decode to PCM16) → yield fixed-size chunks.

    No system ffmpeg needed.
    """

    ffmpeg_exe = get_ffmpeg_path()

    print("\n🌐 Streaming MP3 over HTTP...")
    print("🟦 Using embedded ffmpeg:", ffmpeg_exe)

    # Start ffmpeg process
    process = subprocess.Popen(
        [
            ffmpeg_exe,
            "-i", url,              # read from URL directly
            "-vn",                  # no video
            "-acodec", "pcm_s16le", # PCM16
            "-ac", "1",             # mono
            "-ar", "16000",         # 16kHz
            "-f", "s16le",          # raw PCM
            "pipe:1"                # output to stdout
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0
    )

    print("🎧 Decoding MP3 → PCM16 using ffmpeg...")
    print("📡 Streaming chunks...")

    while True:
        chunk = process.stdout.read(chunk_bytes)
        if not chunk:
            break
        yield chunk