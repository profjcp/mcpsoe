from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Tuple
import time
import numpy as np


@dataclass
class GraphRAGResult:
    context: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    graph_trace: Dict[str, Any] = field(default_factory=dict)
    timing_ms: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0


class GraphRAGAgent:
    """
    MVP GraphRAG Agent (Sprint 2)
    - Recupera top-k inicial desde FAISS
    - Expande contexto con vecinos del grafo de chunks
    - Retorna contexto consolidado + trazabilidad
    """

    def __init__(
        self,
        faiss_index,
        chunks: List[str],
        graph_index: Dict[int, List[int]],
        embed_query_fn: Callable[[str], List[float]],
        top_k: int = 5,
        max_neighbors_per_chunk: int = 2,
    ):
        self.faiss_index = faiss_index
        self.chunks = chunks
        self.graph_index = graph_index or {}
        self.embed_query_fn = embed_query_fn
        self.top_k = top_k
        self.max_neighbors_per_chunk = max_neighbors_per_chunk

    def _search_seed_chunks(self, question: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        q_emb = self.embed_query_fn(question)
        q_np = np.array([q_emb], dtype="float32")
        distances, indices = self.faiss_index.search(q_np, self.top_k)
        return q_np, distances, indices

    def _expand_with_graph(self, seed_indices: List[int]) -> List[int]:
        expanded = []
        seen = set()

        for idx in seed_indices:
            if idx < 0:
                continue
            if idx not in seen:
                expanded.append(idx)
                seen.add(idx)

            neighbors = self.graph_index.get(int(idx), [])[: self.max_neighbors_per_chunk]
            for n in neighbors:
                if n not in seen and 0 <= n < len(self.chunks):
                    expanded.append(int(n))
                    seen.add(int(n))

        return expanded

    def retrieve_with_graph(self, question: str) -> GraphRAGResult:
        t0 = time.time()

        q_np, distances, indices = self._search_seed_chunks(question)
        seed_indices = [int(i) for i in indices[0] if int(i) >= 0]
        expanded_indices = self._expand_with_graph(seed_indices)

        retrieval_ms = (time.time() - t0) * 1000.0

        relevant_chunks = []
        sources = []

        for rank, idx in enumerate(expanded_indices):
            if 0 <= idx < len(self.chunks):
                chunk = self.chunks[idx]
                relevant_chunks.append(chunk)
                sources.append(
                    {
                        "source_type": "chunk",
                        "doc_id": f"chunk_{idx}",
                        "title": "Base documental GraphRAG",
                        "section": f"graph_chunk_rank_{rank+1}",
                        "snippet": chunk[:240],
                    }
                )

        context = (
            "\n\n---\n\n".join(relevant_chunks)
            if relevant_chunks
            else "No se encontró información relevante en los documentos."
        )

        confidence = 0.0
        if len(seed_indices) > 0:
            confidence = min(1.0, 0.5 + 0.05 * len(expanded_indices))

        return GraphRAGResult(
            context=context,
            sources=sources,
            graph_trace={
                "seed_indices": seed_indices,
                "expanded_indices": expanded_indices,
                "graph_enabled": True,
                "top_k": self.top_k,
                "max_neighbors_per_chunk": self.max_neighbors_per_chunk,
            },
            timing_ms={
                "graph_retrieval": retrieval_ms,
            },
            confidence=confidence,
        )
