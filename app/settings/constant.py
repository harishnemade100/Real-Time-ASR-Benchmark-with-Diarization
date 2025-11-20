# app/settings/constants.py
# Put your real API keys here before running.
# Keep this file out of public repos (add to .gitignore).

DEEPGRAM_API_KEY = "5959e1b97f7456aa4dd36a1052102ffa77020f62"
ASSEMBLYAI_API_KEY = "70bf8747b26746ce8627c006e5960ff6"

# Which provider to use by default: "deepgram" or "assemblyai"
DEFAULT_PROVIDER = "deepgram"

# Podcast / audio URL to stream
PODCAST_URL = "https://stitcher2.acast.com/livestitches/7dd62dcce3af2ebc524af43c7f5d92f4.mp3?aid=66c61a87ad4561713b6a530d&chid=66715b013d8df9a86f181063&ci=kBm9rIl4FLJIVwRAe8ylRVOcK50d9xY8qhvanUGyjtXfTX_oT-BOBQ%3D%3D&pf=rss&range=bytes%3D0-&sv=sphinx%401.266.0&uid=056ff82778d49ab6682cd77940073f17&Expires=1762781988582&Key-Pair-Id=K38CTQXUSD0VVB&Signature=l6yoxdQMiHRyR45xu6Gjr6JBHknMEUIdfNN7RcaYYgT5Fpao7MwTHVrhPsvGvU0taRHMmlce8Mlj3bd0lV9dOteyfj3Wk6GbKUZ21EcjtPsYSNKjRBaLUjX7tvCjCp73IrEA4yueOl6qYPR9RS9d6Ete7nFAw7pvWPyFWdCjiP6aQIolVt0UcoQPMhYjD5hAlSjgCLHo~jBmm1CPU-sbJOtRxkAuj9a49Yn-X-Z2BZWzitnizkSrJ7VE5Xh-bx1Hui9mKfYdyXlTDyOJLLuDOQifGjIx-OpzWVABVs3dj1L4yGqMQjLcPxpdG43GPcHaWzOAFRx4KmNfIUqiPMBc2A__"

# Audio clip selection (seconds)
START_SEC = 450.0   # example: 7 minutes 30s
DURATION_SEC = 300.0  # 5 minutes

# Segment window (seconds) used in metrics
SEGMENT_SECONDS = 6.0

# Reference transcript CSV (create manually)
REFERENCE_CSV = "data/reference_segments.csv"
