from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable
import time
import numpy as np


@dataclass
class DocRAGAgentResult:
    answer: str
    confidence: float
    sources: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_context: str = ""
    timings_ms: Dict[str, float] = field(default_factory=dict)


from retrieval.hybrid_retriever import HybridRetriever, ACCESS_HIERARCHY

class DocRAGAgent:
    """
    Agente de RAG documental con búsqueda híbrida (BM25 + FAISS + RRF), metadatos y filtrado de acceso.
    """

    def __init__(
        self,
        faiss_index,
        chunks: List[Any],
        embed_query_fn: Callable[[str], List[float]],
        build_chain_fn: Callable[[], Any],
        top_k: int = 5,
        reranker_model_name: str = None,
    ):
        self.faiss_index = faiss_index
        self.chunks = chunks
        self.embed_query_fn = embed_query_fn
        self.build_chain_fn = build_chain_fn
        self.top_k = top_k
        self.hybrid_retriever = HybridRetriever(
            faiss_index=faiss_index,
            chunks=chunks,
            embed_query_fn=embed_query_fn,
            top_k=top_k,
            reranker_model_name=reranker_model_name,
        )

    def retrieve(self, question: str, user_access_level: str = "publico"):
        results, retrieval_ms = self.hybrid_retriever.search(
            query=question,
            user_access_level=user_access_level,
        )

        q_emb = self.embed_query_fn(question)
        q_np = np.array([q_emb], dtype="float32")

        relevant_chunks = []
        sources = []

        for rank, res in enumerate(results):
            chunk_text = res.get("text", "")
            meta = res.get("metadata", {})
            relevant_chunks.append(chunk_text)
            sources.append(
                {
                    "source_type": "hybrid_chunk",
                    "doc_id": meta.get("doc_id", f"chunk_{res.get('chunk_index', rank)}"),
                    "title": meta.get("titulo", "Documento Normativo"),
                    "section": meta.get("articulo", f"rank_{rank+1}"),
                    "categoria": meta.get("categoria", "General"),
                    "nivel_acceso": meta.get("nivel_acceso", "publico"),
                    "rrf_score": res.get("rrf_score", 0.0),
                    "snippet": chunk_text[:240],
                }
            )

        context = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else "No se encontró información relevante en los documentos a los que tiene acceso."
        return context, sources, retrieval_ms, q_np

    async def generate(self, question: str, context: str, few_shot_examples: str = ""):
        t0 = time.time()
        chain = self.build_chain_fn()
        full_response = ""
        async for chunk in chain.astream(
            {
                "context": context,
                "question": question,
                "few_shot_examples": few_shot_examples,
            }
        ):
            full_response += chunk
            yield chunk, None

        generation_ms = (time.time() - t0) * 1000.0
        yield None, generation_ms
