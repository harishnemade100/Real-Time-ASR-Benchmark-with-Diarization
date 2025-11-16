#!/usr/bin/env bash
# Usage: ./extract_audio.sh "PODCAST_URL" <start_seconds> <duration_seconds>
URL="${1:-}"
START="${2:-450}"
DURATION="${3:-300}"
OUT="app/data/audio_clip.wav"
if [ -z "$URL" ]; then
  echo "Usage: $0 PODCAST_URL START_SEC DURATION_SEC"
  exit 1
fi
mkdir -p data
ffmpeg -ss "$START" -i "$URL" -t "$DURATION" -ar 16000 -ac 1 -f wav "$OUT" -y
echo "Wrote $OUT"