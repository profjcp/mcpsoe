from dataclasses import dataclass, field
from typing import Dict, Any, List
import time


@dataclass
class AgentResult:
    answer_text: str
    answer_mode: str
    confidence: float = 0.0
    sources: List[Dict[str, Any]] = field(default_factory=list)
    routing_trace: Dict[str, Any] = field(default_factory=dict)
    timing_ms: Dict[str, float] = field(default_factory=dict)
    knowledge_context: str = ""
    question_embedding_np: Any = None


class MultiAgentOrchestrator:
    """
    Orquestador de Sprint 1:
    GUIDANCE -> FAQ -> CACHE -> RAG_DOC
    """

    def __init__(
        self,
        faq_agent,
        doc_rag_agent,
        categorize_fn,
        needs_guidance_fn,
        build_guidance_fn,
        qa_cache_ref: Dict[str, str],
    ):
        self.faq_agent = faq_agent
        self.doc_rag_agent = doc_rag_agent
        self.categorize_fn = categorize_fn
        self.needs_guidance_fn = needs_guidance_fn
        self.build_guidance_fn = build_guidance_fn
        self.qa_cache_ref = qa_cache_ref

    def route_pre_llm(self, question: str) -> AgentResult:
        t0 = time.time()
        categories = self.categorize_fn(question)

        routing_trace = {
            "categories": categories,
            "guidance_triggered": False,
            "faq_checked": False,
            "faq_confidence": 0.0,
            "cache_hit": False,
            "rag_used": False,
        }

        if self.needs_guidance_fn(question, categories):
            routing_trace["guidance_triggered"] = True
            return AgentResult(
                answer_text=self.build_guidance_fn(),
                answer_mode="GUIDANCE",
                confidence=1.0,
                sources=[],
                routing_trace=routing_trace,
                timing_ms={"total": (time.time() - t0) * 1000.0},
            )

        routing_trace["faq_checked"] = True
        faq_result = self.faq_agent.run(question, categories)
        routing_trace["faq_confidence"] = float(faq_result.confidence)

        if faq_result.found:
            return AgentResult(
                answer_text=faq_result.answer,
                answer_mode="FAQ",
                confidence=float(faq_result.confidence),
                sources=faq_result.sources,
                routing_trace=routing_trace,
                timing_ms={"total": (time.time() - t0) * 1000.0},
            )

        if question in self.qa_cache_ref:
            routing_trace["cache_hit"] = True
            return AgentResult(
                answer_text=self.qa_cache_ref[question],
                answer_mode="CACHE",
                confidence=1.0,
                sources=[],
                routing_trace=routing_trace,
                timing_ms={"total": (time.time() - t0) * 1000.0},
            )

        routing_trace["rag_used"] = True
        context, sources, retrieval_ms, q_np = self.doc_rag_agent.retrieve(question)
        return AgentResult(
            answer_text="",
            answer_mode="RAG_DOC",
            confidence=0.0,
            sources=sources,
            routing_trace=routing_trace,
            timing_ms={"retrieval": retrieval_ms, "pre_route_total": (time.time() - t0) * 1000.0},
            knowledge_context=context,
            question_embedding_np=q_np,
        )
