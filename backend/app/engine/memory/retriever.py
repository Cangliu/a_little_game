"""BM25 Retriever — lightweight keyword-based memory search.

Implements a simplified BM25 scoring algorithm for Chinese text
using character n-grams. No external dependencies required.

Since a single game session has at most a few hundred memory entries,
brute-force iteration is fast enough (<10ms).
"""
from __future__ import annotations

import math
import re
from typing import Optional


class BM25Retriever:
    """Simple BM25 implementation using character bigrams for Chinese text.

    Design choices:
    - Character bigrams instead of word segmentation (no jieba dependency)
    - Augmented with keyword extraction (Chinese punctuation boundaries)
    - BM25 parameters: k1=1.5, b=0.75 (standard)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._documents: list = []  # [{text, tokens, metadata...}]
        self._doc_lengths: list = []
        self._avg_dl: float = 0.0
        self._idf: dict = {}  # {token: idf_score}
        self._indexed = False

    def index(self, documents: list) -> None:
        """Build index from a list of memory entries.

        Each document should be a dict with at least a 'text' field.
        Additional fields are preserved and returned in search results.
        """
        self._documents = []
        self._doc_lengths = []

        for doc in documents:
            text = doc.get("text", "")
            tokens = self._tokenize(text)
            self._documents.append({
                **doc,
                "_tokens": tokens,
                "_token_set": set(tokens),
            })
            self._doc_lengths.append(len(tokens))

        n = len(self._documents)
        if n == 0:
            self._indexed = True
            return

        self._avg_dl = sum(self._doc_lengths) / n

        # Calculate IDF for all tokens
        token_doc_count: dict = {}
        for doc in self._documents:
            for token in doc["_token_set"]:
                token_doc_count[token] = token_doc_count.get(token, 0) + 1

        self._idf = {}
        for token, df in token_doc_count.items():
            # Standard BM25 IDF formula
            self._idf[token] = math.log((n - df + 0.5) / (df + 0.5) + 1)

        self._indexed = True

    def search(self, query: str, top_k: int = 5) -> list:
        """Search for most relevant documents given a query.

        Returns top_k documents sorted by BM25 score (highest first).
        Each result includes the original document fields plus a '_score' field.
        """
        if not self._indexed or not self._documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = []
        for i, doc in enumerate(self._documents):
            score = self._score_document(query_tokens, doc, i)
            if score > 0:
                scores.append((score, i))

        # Sort by score descending
        scores.sort(key=lambda x: -x[0])

        results = []
        for score, idx in scores[:top_k]:
            doc = self._documents[idx]
            # Return doc without internal fields
            result = {k: v for k, v in doc.items() if not k.startswith("_")}
            result["_score"] = round(score, 4)
            results.append(result)

        return results

    def _score_document(self, query_tokens: list, doc: dict, doc_idx: int) -> float:
        """Calculate BM25 score for a single document."""
        score = 0.0
        dl = self._doc_lengths[doc_idx]
        doc_tokens = doc["_tokens"]

        # Count term frequencies in document
        tf_map: dict = {}
        for t in doc_tokens:
            tf_map[t] = tf_map.get(t, 0) + 1

        for qt in query_tokens:
            if qt not in self._idf:
                continue
            tf = tf_map.get(qt, 0)
            if tf == 0:
                continue

            idf = self._idf[qt]
            # BM25 TF normalization
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / self._avg_dl)
            score += idf * (numerator / denominator)

        return score

    @staticmethod
    def _tokenize(text: str) -> list:
        """Tokenize Chinese text into character bigrams + keywords.

        Strategy:
        1. Extract Chinese character bigrams (overlapping)
        2. Extract whole "words" between punctuation (1-4 chars)
        3. Combine for better recall
        """
        if not text:
            return []

        # Remove punctuation for bigram extraction
        clean = re.sub(r'[^\u4e00-\u9fff\w]', ' ', text)
        chars = [c for c in clean if c.strip()]

        tokens = []

        # Character bigrams
        for i in range(len(chars) - 1):
            tokens.append(chars[i] + chars[i + 1])

        # Also add individual characters for short queries
        for c in chars:
            if '\u4e00' <= c <= '\u9fff':
                tokens.append(c)

        # Extract keyword-like segments (between punctuation, 2-4 chars)
        segments = re.split(r'[，。！？、；：""''（）\s,.\!\?\;\:\(\)\[\]]+', text)
        for seg in segments:
            seg = seg.strip()
            if 2 <= len(seg) <= 6:
                tokens.append(seg)

        return tokens


class HybridRetriever:
    """BM25 + Embedding hybrid retriever.

    Combines keyword matching (BM25) with semantic similarity (embedding)
    for better recall on Chinese narrative text.

    score = alpha * bm25_normalized + (1 - alpha) * cosine_similarity

    Graceful degradation: if embedding model is unavailable,
    falls back to pure BM25 automatically.
    """

    def __init__(self, alpha: float = 0.4):
        self._bm25 = BM25Retriever()
        self._embedding = None  # Lazy init
        self._alpha = alpha

    def _ensure_embedding(self):
        """Lazy-init embedding retriever."""
        if self._embedding is None:
            from .embedding_retriever import EmbeddingRetriever
            self._embedding = EmbeddingRetriever()
        return self._embedding

    def index(self, documents: list) -> None:
        """Build BM25 index (embedding is query-time, no index needed)."""
        self._bm25.index(documents)

    def search(self, query: str, top_k: int = 5) -> list:
        """Hybrid search combining BM25 and embedding scores.

        Returns top_k documents sorted by combined score.
        If embedding is unavailable, falls back to pure BM25.
        """
        if not self._bm25._indexed or not self._bm25._documents:
            return []

        documents = self._bm25._documents

        # Step 1: BM25 scores for all documents
        query_tokens = self._bm25._tokenize(query)
        if not query_tokens:
            return []

        bm25_scores = []
        for i, doc in enumerate(documents):
            score = self._bm25._score_document(query_tokens, doc, i)
            bm25_scores.append(score)

        # Normalize BM25 scores to [0, 1]
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        if max_bm25 > 0:
            bm25_normalized = [s / max_bm25 for s in bm25_scores]
        else:
            bm25_normalized = [0.0] * len(bm25_scores)

        # Step 2: Embedding scores (if available)
        embedding_retriever = self._ensure_embedding()
        emb_scores = [0.0] * len(documents)
        use_embedding = False

        if embedding_retriever.available:
            # Get raw document dicts (without internal fields)
            raw_docs = [
                {k: v for k, v in d.items() if not k.startswith("_")}
                for d in documents
            ]
            emb_results = embedding_retriever.search(
                query, raw_docs, top_k=len(documents)
            )
            if emb_results:
                use_embedding = True
                for idx, score in emb_results:
                    if 0 <= idx < len(emb_scores):
                        emb_scores[idx] = score

        # Step 3: Combine scores
        alpha = self._alpha if use_embedding else 1.0
        combined_scores = []
        for i in range(len(documents)):
            combined = alpha * bm25_normalized[i] + (1 - alpha) * emb_scores[i]
            if combined > 0:
                combined_scores.append((combined, i))

        # Sort by combined score descending
        combined_scores.sort(key=lambda x: -x[0])

        results = []
        for score, idx in combined_scores[:top_k]:
            doc = documents[idx]
            result = {k: v for k, v in doc.items() if not k.startswith("_")}
            result["_score"] = round(score, 4)
            results.append(result)

        return results
