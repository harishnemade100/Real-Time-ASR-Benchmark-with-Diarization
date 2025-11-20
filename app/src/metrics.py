# app/src/metrics.py
"""
WER (Word Error Rate) utility
Returns S, I, D, N for each comparison.
"""

from typing import Tuple
import numpy as np
import re

def normalize_text(s: str) -> str:
    s2 = s.lower()
    s2 = re.sub(r"[^a-z0-9\s]+", "", s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return s2

def compute_wer(ref: str, hyp: str) -> Tuple[int, int, int, int]:
    """
    Compute S, I, D, N using Levenshtein DP on tokens.
    Returns (S, I, D, N)
    """
    r_tokens = normalize_text(ref).split()
    h_tokens = normalize_text(hyp).split()
    N = len(r_tokens)
    if N == 0:
        return 0, len(h_tokens), 0, 0  # handle empty ref

    d = np.zeros((N+1, len(h_tokens)+1), dtype=int)
    for i in range(1, N+1):
        d[i,0] = i
    for j in range(1, len(h_tokens)+1):
        d[0,j] = j

    for i in range(1, N+1):
        for j in range(1, len(h_tokens)+1):
            if r_tokens[i-1] == h_tokens[j-1]:
                d[i,j] = d[i-1,j-1]
            else:
                sub = d[i-1,j-1] + 1
                ins = d[i,j-1] + 1
                delete = d[i-1,j] + 1
                d[i,j] = min(sub, ins, delete)

    i, j = N, len(h_tokens)
    S = I = D = 0
    while i > 0 or j > 0:
        if i>0 and j>0 and r_tokens[i-1] == h_tokens[j-1]:
            i -= 1
            j -= 1
        else:
            if i>0 and j>0 and d[i,j] == d[i-1,j-1] + 1:
                S += 1
                i -= 1
                j -= 1
            elif j>0 and d[i,j] == d[i,j-1] + 1:
                I += 1
                j -= 1
            elif i>0 and d[i,j] == d[i-1,j] + 1:
                D += 1
                i -= 1
            else:
                # fallback
                if i>0:
                    D += 1; i -= 1
                elif j>0:
                    I += 1; j -= 1
    return S, I, D, N
