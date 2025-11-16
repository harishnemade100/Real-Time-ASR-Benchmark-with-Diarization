#!/usr/bin/env bash
# Usage: run_assemblyai.sh "PODCAST_URL" START DURATION
URL="$1"
START="${2:-450}"
DURATION="${3:-300}"

# --- Modification Starts Here ---
# Step 1: Execute a Python command to read and print the API key.
# This assumes your settings file is importable and has a variable named ASSEMBLYAI_API_KEY.
# NOTE: Replace 'app.settings.constant' with the actual module path if different.
# This command captures the key's value into the SHELL variable ASSEMBLYAI_API_KEY_VALUE
ASSEMBLYAI_API_KEY_VALUE=$(python -c "from app.settings.constant import ASSEMBLYAI_API_KEY; print(ASSEMBLYAI_API_KEY)")
# Step 2: Now check the retrieved value
if [ -z "$ASSEMBLYAI_API_KEY_VALUE" ]; then
  echo "Failed to retrieve ASSEMBLYAI_API_KEY from app/settings/constant.py"
  exit 1
fi
# Step 3: Use the retrieved value in the python command
python src/stream_benchmark.py --provider assemblyai --api_key "$ASSEMBLYAI_API_KEY_VALUE" --url "$URL" --start "$START" --duration "$DURATION" --reference_csv app/data/reference_segments.csv