"""
diarization_parser.py

Vendor-agnostic helpers to convert vendor JSON events into simple diarized utterances:
list of dicts: { speaker: "0", start: float, end: float, text: "..." }
"""

from typing import List, Dict, Any

def parse_deepgram_event(event: Dict[str, Any]) -> List[Dict[str,Any]]:
    """
    Best-effort parsing for Deepgram listen events.
    Returns list of utterances (may be empty).
    """
    utts = []
    # Deepgram typically sends 'channel' or 'channels' with alternatives and words with speaker tags
    # This function attempts to find words and group by speaker into one utterance
    def extract_words(obj):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k == 'words' and isinstance(v, list):
                    return v
                else:
                    r = extract_words(v)
                    if r:
                        return r
        elif isinstance(obj, list):
            for item in obj:
                r = extract_words(item)
                if r:
                    return r
        return None
    words = extract_words(event) or []
    if words:
        groups = {}
        for w in words:
            sp = str(w.get('speaker','0'))
            t0 = float(w.get('start',0.0))
            t1 = float(w.get('end', t0))
            text = w.get('word') or w.get('text') or ""
            if sp not in groups:
                groups[sp] = {"speaker":sp, "start":t0, "end":t1, "text":[text]}
            else:
                groups[sp]["end"] = t1
                groups[sp]["text"].append(text)
        for sp, v in groups.items():
            utts.append({
                "speaker": v["speaker"],
                "start": v["start"],
                "end": v["end"],
                "text": " ".join(v["text"]).strip()
            })
    # fallback: some messages include alternatives.text and possibly a speaker label
    if not utts:
        alt = None
        if isinstance(event, dict):
            alt = event.get("alternative") or event.get("alternatives")
            if isinstance(alt, list) and len(alt)>0:
                alt = alt[0]
            if isinstance(alt, dict):
                text = alt.get("transcript") or alt.get("text") or alt.get("transcript")
                if text:
                    sp = str(event.get('speaker','0'))
                    utts.append({"speaker": sp, "start": 0.0, "end": 0.0, "text": text})
    return utts

def parse_assemblyai_event(event: Dict[str, Any]) -> List[Dict[str,Any]]:
    """
    Parse AssemblyAI Realtime event to diarized utterances.
    AssemblyAI sends 'type': 'PartialTranscript' / 'FinalTranscript' with 'text' and 'speaker' sometimes.
    """
    utts = []
    tp = event.get('type','')
    if isinstance(event, dict) and tp.lower().endswith('transcript'):
        text = event.get('text') or ""
        sp = event.get('speaker') or event.get('speaker_label') or "0"
        # AssemblyAI may include timestamps per word in 'words' field
        start = event.get('start',0.0)
        end = event.get('end',0.0)
        utts.append({"speaker": str(sp), "start": start, "end": end, "text": text})
    return utts
