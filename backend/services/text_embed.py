from __future__ import annotations
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_model():
    """
    Load CLIP model using sentence-transformers (lightweight).
    Uses 'clip-ViT-B-32' which is compatible with OpenAI CLIP embeddings.
    Cached to load only once.
    """
    return SentenceTransformer('clip-ViT-B-32')

def get_text_embedding(text: str) -> list[float]:
    """
    Encode text with CLIP and L2-normalize so it is cosine-compatible
    with image embeddings we stored.
    Returns a Python list[float] (length 512) for psycopg2 vector casting.
    """
    model = _get_model()
    
    # Encode text to embedding
    embedding = model.encode(text, convert_to_numpy=True)
    
    # L2 normalize
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist()
