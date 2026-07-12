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
        graph_rag_agent,
        categorize_fn,
        needs_guidance_fn,
        build_guidance_fn,
        qa_cache_ref: Dict[str, str],
        enable_graph_rag: bool = False,
    ):
        self.faq_agent = faq_agent
        self.doc_rag_agent = doc_rag_agent
        self.graph_rag_agent = graph_rag_agent
        self.categorize_fn = categorize_fn
        self.needs_guidance_fn = needs_guidance_fn
        self.build_guidance_fn = build_guidance_fn
        self.qa_cache_ref = qa_cache_ref
        self.enable_graph_rag = enable_graph_rag

    def route_pre_llm(self, question: str) -> AgentResult:
        t0 = time.time()
        categories = self.categorize_fn(question)

        routing_trace = {
            "route_version": "sprint2.v2",
            "categories": categories,
            "selected_mode": None,
            "decision_reason": "",
            "fallbacks_applied": [],
            "guidance_triggered": False,
            "faq_checked": False,
            "faq_confidence": 0.0,
            "cache_hit": False,
            "rag_used": False,
            "graph_rag_used": False,
            "decision_timing_ms": {},
        }

        t_guidance = time.time()
        if self.needs_guidance_fn(question, categories):
            routing_trace["guidance_triggered"] = True
            routing_trace["selected_mode"] = "GUIDANCE"
            routing_trace["decision_reason"] = "needs_guidance_fn=True"
            routing_trace["decision_timing_ms"]["guidance_check"] = (time.time() - t_guidance) * 1000.0
            return AgentResult(
                answer_text=self.build_guidance_fn(),
                answer_mode="GUIDANCE",
                confidence=1.0,
                sources=[],
                routing_trace=routing_trace,
                timing_ms={"total": (time.time() - t0) * 1000.0},
            )

        routing_trace["decision_timing_ms"]["guidance_check"] = (time.time() - t_guidance) * 1000.0

        t_faq = time.time()
        routing_trace["faq_checked"] = True
        faq_result = self.faq_agent.run(question, categories)
        routing_trace["faq_confidence"] = float(faq_result.confidence)
        routing_trace["decision_timing_ms"]["faq_check"] = (time.time() - t_faq) * 1000.0

        if faq_result.found:
            routing_trace["selected_mode"] = "FAQ"
            routing_trace["decision_reason"] = "faq_match_found"
            return AgentResult(
                answer_text=faq_result.answer,
                answer_mode="FAQ",
                confidence=float(faq_result.confidence),
                sources=faq_result.sources,
                routing_trace=routing_trace,
                timing_ms={"total": (time.time() - t0) * 1000.0},
            )

        t_cache = time.time()
        if question in self.qa_cache_ref:
            routing_trace["cache_hit"] = True
            routing_trace["selected_mode"] = "CACHE"
            routing_trace["decision_reason"] = "exact_question_in_cache"
            routing_trace["decision_timing_ms"]["cache_check"] = (time.time() - t_cache) * 1000.0
            return AgentResult(
                answer_text=self.qa_cache_ref[question],
                answer_mode="CACHE",
                confidence=1.0,
                sources=[],
                routing_trace=routing_trace,
                timing_ms={"total": (time.time() - t0) * 1000.0},
            )

        routing_trace["decision_timing_ms"]["cache_check"] = (time.time() - t_cache) * 1000.0

        use_graph_rag = (
            self.enable_graph_rag
            and self.graph_rag_agent is not None
            and any(cat in {"Investigacion", "Academica"} for cat in categories)
        )

        if use_graph_rag:
            graph_result = self.graph_rag_agent.retrieve_with_graph(question)
            routing_trace["graph_rag_used"] = True
            routing_trace["selected_mode"] = "GRAPH_RAG"
            routing_trace["decision_reason"] = "enable_graph_rag=True and category in {Investigacion,Academica}"
            return AgentResult(
                answer_text="",
                answer_mode="GRAPH_RAG",
                confidence=float(graph_result.confidence),
                sources=graph_result.sources,
                routing_trace={**routing_trace, "graph_trace": graph_result.graph_trace},
                timing_ms={**graph_result.timing_ms, "pre_route_total": (time.time() - t0) * 1000.0},
                knowledge_context=graph_result.context,
                question_embedding_np=None,
            )

        routing_trace["rag_used"] = True
        routing_trace["selected_mode"] = "RAG_DOC"
        routing_trace["decision_reason"] = "fallback_to_doc_rag"
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
