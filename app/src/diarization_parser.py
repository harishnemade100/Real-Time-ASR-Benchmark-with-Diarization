# app/src/diarization_parser.py
"""
Vendor-agnostic parsing helpers.
Converts vendor JSON events into a list of utterances:
    [{ "speaker": "0", "start": 0.0, "end": 1.2, "text": "..." }, ...]
"""

from typing import List, Dict, Any

def parse_deepgram_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    utts = []
    def extract_words(obj):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k == 'words' and isinstance(v, list):
                    return v
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
            t0 = float(w.get('start', 0.0))
            t1 = float(w.get('end', t0))
            text = w.get('word') or w.get('text') or ""
            if sp not in groups:
                groups[sp] = {"speaker": sp, "start": t0, "end": t1, "text": [text]}
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
    else:
        # fallback: try alternatives
        alt = None
        if isinstance(event, dict):
            alt = event.get("alternative") or event.get("alternatives")
            if isinstance(alt, list) and len(alt) > 0:
                alt = alt[0]
            if isinstance(alt, dict):
                text = alt.get("transcript") or alt.get("text")
                if text:
                    sp = str(event.get('speaker','0'))
                    utts.append({"speaker": sp, "start": 0.0, "end": 0.0, "text": text})
    return utts


def parse_assemblyai_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    utts = []
    tp = event.get('type','')
    if isinstance(event, dict) and tp.lower().endswith('transcript'):
        text = event.get('text') or ""
        sp = event.get('speaker') or event.get('speaker_label') or "0"
        start = event.get('start', 0.0)
        end = event.get('end', 0.0)
        utts.append({"speaker": str(sp), "start": start, "end": end, "text": text})
    return utts
