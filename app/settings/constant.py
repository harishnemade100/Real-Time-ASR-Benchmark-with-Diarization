SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes

# chunk ms for sending - smaller => lower latency but more messages
CHUNK_MS = 320

TRANSCRIPTS_JSONL = "transcripts.jsonl"
METRICS_CSV = "app/data/sample_metrics_{provider}.csv"

DEEPGRAM_API_KEY="5bddc92f4a8bfc831ee55d96f83a66b3d9f80d8f"
ASSEMBLYAI_API_KEY="70bf8747b26746ce8627c006e5960ff6"