import time
import math
import numpy as np
from typing import List, Dict, Any, Tuple, Callable

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False

ACCESS_HIERARCHY = {
    "publico": 1,
    "estudiante": 2,
    "docente": 3,
    "admin": 4,
}

def tokenize_spanish(text: str) -> List[str]:
    """Tokenizador ligero para BM25 en español."""
    import re
    text = (text or "").lower()
    return [w for w in re.split(r"\W+", text) if len(w) > 1]


class HybridRetriever:
    """
    Recuperador Híbrido (BM25 Léxico + FAISS Vectorial) con RRF y Reranking Cross-Encoder.
    - Captura términos exactos (códigos, números de artículo) mediante BM25.
    - Captura conceptos semánticos mediante FAISS.
    - Aplica Reciprocal Rank Fusion (RRF).
    - Aplica filtro estricto por nivel_acceso.
    - Opcional: Re-clasifica los mejores candidatos usando Cross-Encoder.
    """

    def __init__(
        self,
        faiss_index,
        chunks: List[Any],
        embed_query_fn: Callable[[str], List[float]],
        top_k: int = 5,
        reranker_model_name: str = None,
    ):
        self.faiss_index = faiss_index
        self.chunks = chunks
        self.embed_query_fn = embed_query_fn
        self.top_k = top_k
        self.bm25 = None
        self.reranker = None

        # Inicializar BM25 si la librería está disponible y hay chunks
        if HAS_BM25 and self.chunks:
            tokenized_corpus = []
            for item in self.chunks:
                text = item.get("text", "") if isinstance(item, dict) else str(item)
                tokenized_corpus.append(tokenize_spanish(text))
            self.bm25 = BM25Okapi(tokenized_corpus)

        # Inicializar Reranker si se especifica modelo
        if HAS_CROSS_ENCODER and reranker_model_name:
            try:
                self.reranker = CrossEncoder(reranker_model_name)
            except Exception:
                self.reranker = None

    def search(
        self,
        query: str,
        user_access_level: str = "publico",
        rrf_k: int = 60,
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Ejecuta la búsqueda híbrida y devuelve los top_k chunks autorizados.
        """
        t0 = time.time()
        user_level_val = ACCESS_HIERARCHY.get(user_access_level.lower(), 1)
        total_chunks = len(self.chunks)

        if total_chunks == 0:
            return [], 0.0

        search_n = min(total_chunks, max(self.top_k * 4, 25))

        # 1. Búsqueda Vectorial (FAISS)
        q_emb = self.embed_query_fn(query)
        q_np = np.array([q_emb], dtype="float32")
        _, faiss_indices = self.faiss_index.search(q_np, search_n)
        vector_rank_map = {int(idx): rank for rank, idx in enumerate(faiss_indices[0]) if 0 <= idx < total_chunks}

        # 2. Búsqueda Léxica (BM25)
        bm25_rank_map = {}
        if self.bm25:
            tokens = tokenize_spanish(query)
            scores = self.bm25.get_scores(tokens)
            top_bm25_indices = np.argsort(scores)[::-1][:search_n]
            bm25_rank_map = {int(idx): rank for rank, idx in enumerate(top_bm25_indices) if scores[idx] > 0}

        # 3. Reciprocal Rank Fusion (RRF)
        all_candidate_indices = set(vector_rank_map.keys()).union(set(bm25_rank_map.keys()))
        rrf_scores = {}

        for idx in all_candidate_indices:
            score = 0.0
            if idx in vector_rank_map:
                score += 1.0 / (rrf_k + vector_rank_map[idx])
            if idx in bm25_rank_map:
                score += 1.0 / (rrf_k + bm25_rank_map[idx])
            rrf_scores[idx] = score

        # Ordenar candidatos por puntuación RRF
        sorted_candidates = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # 4. Filtrado por Nivel de Acceso y Selección de Candidatos
        filtered_results = []
        for idx in sorted_candidates:
            item = self.chunks[idx]
            if isinstance(item, dict):
                text = item.get("text", "")
                meta = item.get("metadata", {})
            else:
                text = str(item)
                meta = {"titulo": "Documento RAG", "doc_id": f"chunk_{idx}", "nivel_acceso": "publico", "articulo": ""}

            chunk_access = meta.get("nivel_acceso", "publico").lower()
            if ACCESS_HIERARCHY.get(chunk_access, 1) <= user_level_val:
                filtered_results.append({
                    "chunk_index": idx,
                    "text": text,
                    "metadata": meta,
                    "rrf_score": rrf_scores[idx],
                })

        # 5. Reranking con Cross-Encoder (si está configurado)
        if self.reranker and len(filtered_results) > 1:
            pairs = [[query, r["text"]] for r in filtered_results[:search_n]]
            scores = self.reranker.predict(pairs)
            for i, score in enumerate(scores):
                filtered_results[i]["rerank_score"] = float(score)
            filtered_results[:search_n] = sorted(
                filtered_results[:search_n], key=lambda x: x.get("rerank_score", 0.0), reverse=True
            )

        elapsed_ms = (time.time() - t0) * 1000.0
        return filtered_results[: self.top_k], elapsed_ms
