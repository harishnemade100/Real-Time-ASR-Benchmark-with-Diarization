# app/src/deepgram_ws.py
"""
Minimal Deepgram WebSocket helper.
Sends raw PCM16LE binary frames to Deepgram's listen endpoint.

Docs: https://developers.deepgram.com/
"""

import json
import websockets

async def connect(api_key: str, model: str = "general", sample_rate: int = 16000, diarize: bool = True):
    """
    Connect to Deepgram listen WebSocket.
    Returns connected websocket.
    """
    query = f"?model={model}&encoding=linear16&sample_rate={sample_rate}&channels=1"
    if diarize:
        query += "&diarize=true"
    url = f"wss://api.deepgram.com/v1/listen{query}"
    headers = [("Authorization", f"Token {api_key}")]
    ws = await websockets.connect(
    url,
    extra_headers=headers,  
    max_size=None
        )
    return ws

async def send_audio(ws, chunk: bytes):
    """
    Send raw PCM16LE chunk as binary frame.
    """
    await ws.send(chunk)

async def close(ws):
    """
    Close stream politely (Deepgram accepts a CloseStream JSON object)
    """
    try:
        await ws.send(json.dumps({"type":"CloseStream"}))
    except Exception:
        pass
    await ws.close()
