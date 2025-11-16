"""
assemblyai_ws.py

Minimal WebSocket client helper for AssemblyAI Realtime.
AssemblyAI expects base64 frames wrapped as JSON {"type":"InputAudio","audio_data":"..."}
and control messages like {"type":"StartStream"} and {"type":"StopStream"}.
"""

import json
import base64
import websockets

async def connect(api_key: str, sample_rate: int = 16000):
    url = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={sample_rate}"
    headers = [("Authorization", api_key)]
    ws = await websockets.connect(url, extra_headers=headers, max_size=None)
    return ws

async def start_stream(ws):
    await ws.send(json.dumps({"type":"StartStream"}))

async def send_audio(ws, chunk: bytes):
    b64 = base64.b64encode(chunk).decode("ascii")
    await ws.send(json.dumps({"type":"InputAudio", "audio_data": b64}))

async def stop_stream(ws):
    try:
        await ws.send(json.dumps({"type":"StopStream"}))
    except Exception:
        pass
    await ws.close()
