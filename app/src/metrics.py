"""
metrics.py - WER & latency helpers
"""

from typing import Tuple
import numpy as np
# NOTE: 'utils' and 'normalize_text' must be defined in your environment/project structure
# from utils import normalize_text 
# Assuming a simple tokenization for demonstration since 'normalize_text' is undefined
def normalize_text(text: str) -> str:
    """Placeholder for text normalization (e.g., lowercasing, removing punctuation)."""
    return text.lower()

def compute_wer(ref: str, hyp: str) -> Tuple[int, int, int, int]:
    """
    Compute S (Substitutions), I (Insertions), D (Deletions), N (Reference Word Count)
    for Word Error Rate (WER) using Levenshtein distance on tokens.
    Returns (S, I, D, N)
    """
    r_tokens = normalize_text(ref).split()
    h_tokens = normalize_text(hyp).split()
    N = len(r_tokens)  # Total number of words in the reference (N)

    # 1. Initialization of the Dynamic Programming (DP) matrix
    # d[i, j] will store the minimum edit distance between r_tokens[:i] and h_tokens[:j]
    d = np.zeros((N + 1, len(h_tokens) + 1), dtype=int)

    # Base cases: cost of turning an empty string into a prefix/suffix
    for i in range(1, N + 1):
        d[i, 0] = i  # Deletions
    for j in range(1, len(h_tokens) + 1):
        d[0, j] = j  # Insertions

    # 2. Filling the DP matrix
    for i in range(1, N + 1):
        for j in range(1, len(h_tokens) + 1):
            if r_tokens[i - 1] == h_tokens[j - 1]:
                # No operation needed (Match)
                d[i, j] = d[i - 1, j - 1]
            else:
                # Calculate costs for possible operations
                substitution = d[i - 1, j - 1] + 1
                insertion = d[i, j - 1] + 1
                deletion = d[i - 1, j] + 1
                # Choose the minimum cost
                d[i, j] = min(substitution, insertion, deletion)

    # 3. Backtracking to find S, I, D counts
    i, j = N, len(h_tokens)
    S = I = D = 0

    while i > 0 or j > 0:
        # Match case
        if i > 0 and j > 0 and r_tokens[i - 1] == h_tokens[j - 1]:
            i -= 1
            j -= 1
        else:
            # Determine the operation that led to d[i,j] (i.e., the one with minimum cost)
            
            # 1. Substitution (d[i-1, j-1] + 1)
            # This check prioritizes substitution over deletion/insertion if costs are equal,
            # which is a common convention for WER calculation.
            if i > 0 and j > 0 and d[i, j] == d[i - 1, j - 1] + 1:
                S += 1
                i -= 1
                j -= 1
            
            # 2. Insertion (d[i, j-1] + 1)
            elif j > 0 and d[i, j] == d[i, j - 1] + 1:
                I += 1
                j -= 1
            
            # 3. Deletion (d[i-1, j] + 1)
            elif i > 0 and d[i, j] == d[i - 1, j] + 1:
                D += 1
                i -= 1
            
            # Fallback/Edge cases (e.g., when reaching the boundaries of the matrix)
            # This part of the original logic handles cases where the minimum cost might be
            # due to reaching a boundary, though the explicit checks above should cover most.
            else:
                if i > 0:
                    D += 1
                    i -= 1
                else: # j > 0
                    I += 1
                    j -= 1
    
    return S, I, D, N

# # --- Example Usage (requires numpy) ---
# if __name__ == '__main__':
#     # You would need to ensure `normalize_text` is correctly implemented for real use.
    
#     reference = "the quick brown fox"
#     hypothesis = "a quick red fox"
    
#     # Expected: S=1 (brown -> red), I=0, D=1 (the -> a is a Sub), N=4
#     # Let's trace:
#     # 'the' vs 'a' -> Sub (S=1)
#     # 'quick' vs 'quick' -> Match
#     # 'brown' vs 'red' -> Sub (S=1)
#     # 'fox' vs 'fox' -> Match
#     # Wait, the Levenshtein will see 'the' vs 'a' as a substitution.
#     # ref: the quick brown fox (4 words)
#     # hyp: a quick red fox (4 words)
    
#     S, I, D, N = compute_wer(reference, hypothesis)
#     WER = (S + I + D) / N if N > 0 else 0
    
#     print(f"Reference: '{reference}'")
#     print(f"Hypothesis: '{hypothesis}'")
#     print(f"Substitutions (S): {S}")
#     print(f"Insertions (I): {I}")
#     print(f"Deletions (D): {D}")
#     print(f"Reference Length (N): {N}")
#     print(f"Word Error Rate (WER): {WER:.4f} ({S+I+D}/{N})")