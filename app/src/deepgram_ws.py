"""
deepgram_ws.py

Minimal WebSocket client helper for Deepgram listen endpoint.

NOTE: This is a lightweight helper. For production use prefer official SDK.
"""

import json
import websockets

async def connect(api_key: str, model: str = "general", sample_rate: int = 16000, diarize: bool = True):
    query = f"?model={model}&encoding=linear16&sample_rate={sample_rate}&channels=1"
    if diarize:
        query += "&diarize=true"
    url = f"wss://api.deepgram.com/v1/listen{query}"
    headers = [("Authorization", f"Token {api_key}")]
    ws = await websockets.connect(url, extra_headers=headers, max_size=None)
    return ws

async def send_audio(ws, chunk: bytes):
    # Deepgram accepts raw binary frames of PCM16LE
    await ws.send(chunk)

async def close(ws):
    # Deepgram accepts a JSON CloseStream object per docs
    try:
        await ws.send(json.dumps({"type":"CloseStream"}))
    except Exception:
        pass
    await ws.close()
