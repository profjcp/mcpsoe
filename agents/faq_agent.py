from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any, Optional
import numpy as np


@dataclass
class AgentSource:
    source_type: str
    doc_id: str
    title: str
    section: str
    snippet: str


@dataclass
class FAQAgentResult:
    found: bool
    answer: str = ""
    confidence: float = 0.0
    matched_category: str = ""
    sources: List[Dict[str, Any]] = field(default_factory=list)


class FAQAgent:
    """
    Agente FAQ semántico.
    Nota: no acopla lógica de carga; recibe callbacks para mantener compatibilidad
    con el backend existente.
    """

    def __init__(
        self,
        faq_files: Dict[str, str],
        load_faqs_fn: Callable[[str, Callable[[str], List[float]]], List[Dict[str, Any]]],
        embed_query_fn: Callable[[str], List[float]],
        threshold: float = 0.75,
    ):
        self.faq_files = faq_files
        self.load_faqs_fn = load_faqs_fn
        self.embed_query_fn = embed_query_fn
        self.threshold = threshold

    @staticmethod
    def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        denom = (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)) + 1e-8
        return float(np.dot(vec_a, vec_b) / denom)

    def _search_in_category(self, question: str, category: str) -> Optional[FAQAgentResult]:
        faq_path = self.faq_files.get(category)
        if not faq_path:
            return None

        faqs = self.load_faqs_fn(faq_path, self.embed_query_fn)
        if not faqs:
            return None

        q_emb = np.array(self.embed_query_fn(question), dtype="float32")
        best_score = -1.0
        best_item = None

        for item in faqs:
            emb = np.array(item.get("embedding", []), dtype="float32")
            if emb.size == 0:
                continue
            score = self._cosine_similarity(q_emb, emb)
            if score > best_score:
                best_score = score
                best_item = item

        if best_item and best_score >= self.threshold:
            answer = f"Pregunta: {best_item.get('pregunta', '')}\nRespuesta: {best_item.get('respuesta', '')}"
            source = AgentSource(
                source_type="faq",
                doc_id=faq_path,
                title=f"FAQ {category}",
                section=best_item.get("pregunta", "")[:120],
                snippet=best_item.get("respuesta", "")[:240],
            )
            return FAQAgentResult(
                found=True,
                answer=answer,
                confidence=best_score,
                matched_category=category,
                sources=[source.__dict__],
            )
        return None

    def run(self, question: str, categories: List[str]) -> FAQAgentResult:
        checked = set()

        for category in categories:
            checked.add(category)
            result = self._search_in_category(question, category)
            if result and result.found:
                return result

        for category in self.faq_files.keys():
            if category in checked:
                continue
            result = self._search_in_category(question, category)
            if result and result.found:
                return result

        return FAQAgentResult(found=False)
