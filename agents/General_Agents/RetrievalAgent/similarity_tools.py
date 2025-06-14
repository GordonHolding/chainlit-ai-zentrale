# similarity_tools.py – lokale Ähnlichkeitsberechnung via Kosinus

import numpy as np

def cosine_similarity(vec1, vec2):
    """
    Berechnet die Kosinus-Ähnlichkeit zwischen zwei Vektoren.
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)
