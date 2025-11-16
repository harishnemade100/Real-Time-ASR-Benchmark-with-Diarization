#!/usr/bin/env bash
# Usage: run_deepgram.sh "PODCAST_URL" START DURATION
URL="$1"
START="${2:-450}"
DURATION="${3:-300}"

# --- Modification: Read key from Python settings file ---
# NOTE: This assumes 'app.settings.constant' is the correct module path
DEEPGRAM_API_KEY_VALUE=$(python -c "from app.settings.constant import DEEPGRAM_API_KEY; print(DEEPGRAM_API_KEY)")

# Check if the value was successfully retrieved
if [ -z "$DEEPGRAM_API_KEY_VALUE" ]; then
    echo "Please set DEEPGRAM_API_KEY in environment or ensure it is correctly defined in app/settings/constant.py"
    exit 1
fi
# --- End Modification ---

# Now run the Python script using the retrieved key value
python src/stream_benchmark.py \
    --provider deepgram \
    --api_key "$DEEPGRAM_API_KEY_VALUE" \
    --url "$URL" \
    --start "$START" \
    --duration "$DURATION" \
    --reference_csv app/data/reference_segments.csv