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


class DocRAGAgent:
    """
    Agente de RAG documental (Sprint 1).
    - Recupera top-k chunks desde índice FAISS.
    - Genera respuesta con LLM chain externo.
    - Expone sources y timings para trazabilidad.
    """

    def __init__(
        self,
        faiss_index,
        chunks: List[str],
        embed_query_fn: Callable[[str], List[float]],
        build_chain_fn: Callable[[], Any],
        top_k: int = 5,
    ):
        self.faiss_index = faiss_index
        self.chunks = chunks
        self.embed_query_fn = embed_query_fn
        self.build_chain_fn = build_chain_fn
        self.top_k = top_k

    def retrieve(self, question: str):
        t0 = time.time()
        q_emb = self.embed_query_fn(question)
        q_np = np.array([q_emb], dtype="float32")
        distances, indices = self.faiss_index.search(q_np, self.top_k)
        retrieval_ms = (time.time() - t0) * 1000.0

        relevant_chunks = []
        sources = []
        for rank, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.chunks):
                chunk = self.chunks[idx]
                relevant_chunks.append(chunk)
                sources.append(
                    {
                        "source_type": "chunk",
                        "doc_id": f"chunk_{idx}",
                        "title": "Base documental RAG",
                        "section": f"chunk_rank_{rank+1}",
                        "snippet": chunk[:240],
                    }
                )

        context = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else "No se encontró información relevante en los documentos."
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
