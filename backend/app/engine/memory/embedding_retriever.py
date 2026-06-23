"""Embedding-based semantic retriever using a local Chinese model.

Uses moka-ai/m3e-base (~200MB) for Chinese short text embeddings.
Lazy-loaded on first use to avoid startup delay.

Graceful degradation: if sentence-transformers is not installed or
model loading fails, all methods return empty results silently.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingRetriever:
    """Semantic retriever using local sentence-transformer model.

    Features:
    - Lazy model loading (first encode call triggers download/load)
    - Cosine similarity search (embeddings are L2-normalized)
    - Graceful fallback: returns empty results if model unavailable
    """

    MODEL_NAME = "moka-ai/m3e-base"

    def __init__(self):
        self._model = None
        self._available: Optional[bool] = None  # None = not yet checked

    def _ensure_model(self) -> bool:
        """Lazy-load the embedding model. Returns True if available."""
        if self._available is not None:
            return self._available

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.MODEL_NAME)
            self._available = True
            logger.info("EmbeddingRetriever loaded model: %s", self.MODEL_NAME)
        except ImportError:
            logger.info(
                "sentence-transformers not installed, "
                "embedding retrieval disabled"
            )
            self._available = False
        except Exception as e:
            logger.warning("Failed to load embedding model: %s", e)
            self._available = False

        return self._available

    @property
    def available(self) -> bool:
        """Whether the embedding model is loaded and ready."""
        if self._available is None:
            return self._ensure_model()
        return self._available

    def encode(self, texts: list[str]):
        """Encode texts into normalized embedding vectors.

        Returns numpy array of shape (len(texts), embed_dim),
        or None if model unavailable.
        """
        if not self._ensure_model():
            return None

        try:
            import numpy as np
            embeddings = self._model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            logger.warning("Embedding encode failed: %s", e)
            return None

    def search(
        self, query: str, documents: list, top_k: int = 5
    ) -> list[tuple[int, float]]:
        """Semantic search: return (doc_index, cosine_similarity) pairs.

        Args:
            query: Search query text
            documents: List of memory dicts with 'text' field
            top_k: Number of top results to return

        Returns:
            List of (index, score) tuples sorted by similarity descending.
            Returns empty list if model unavailable.
        """
        if not documents or not self._ensure_model():
            return []

        try:
            import numpy as np

            doc_texts = [d.get("text", "") for d in documents]
            # Encode query and documents together for efficiency
            all_texts = [query] + doc_texts
            all_embeddings = self.encode(all_texts)

            if all_embeddings is None:
                return []

            query_emb = all_embeddings[0]  # (embed_dim,)
            doc_embs = all_embeddings[1:]  # (n_docs, embed_dim)

            # Cosine similarity (embeddings are already normalized)
            similarities = np.dot(doc_embs, query_emb)

            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]

            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score > 0:
                    results.append((int(idx), score))

            return results
        except Exception as e:
            logger.warning("Embedding search failed: %s", e)
            return []
