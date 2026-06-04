from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any, Optional
import unicodedata
import re
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
        threshold: float = 0.82,
        min_token_overlap: int = 2,
    ):
        self.faq_files = faq_files
        self.load_faqs_fn = load_faqs_fn
        self.embed_query_fn = embed_query_fn
        self.threshold = threshold
        self.min_token_overlap = min_token_overlap

    @staticmethod
    def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        denom = (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)) + 1e-8
        return float(np.dot(vec_a, vec_b) / denom)

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return text

    @staticmethod
    def _tokenize_meaningful(text: str) -> set:
        stopwords = {
            "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "u",
            "que", "como", "cual", "cuales", "es", "son", "en", "por", "para", "del",
            "al", "a", "me", "mi", "tu", "su", "se", "lo", "le", "les"
        }
        normalized = FAQAgent._normalize_text(text)
        tokens = re.findall(r"[a-z0-9]+", normalized)
        return {t for t in tokens if len(t) > 2 and t not in stopwords}

    def _passes_lexical_guardrail(self, question: str, faq_question: str) -> bool:
        q_tokens = self._tokenize_meaningful(question)
        f_tokens = self._tokenize_meaningful(faq_question)
        if not q_tokens or not f_tokens:
            return False
        overlap = q_tokens.intersection(f_tokens)
        return len(overlap) >= self.min_token_overlap

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

        if best_item and best_score >= self.threshold and self._passes_lexical_guardrail(question, best_item.get("pregunta", "")):
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
        normalized_categories = categories or ["Otro"]
        needs_strict_rag_fallback = any(cat in {"Investigacion", "Academica"} for cat in normalized_categories)

        for category in normalized_categories:
            checked.add(category)
            result = self._search_in_category(question, category)
            if result and result.found:
                # Guardrail adicional: para categorías académicas/investigación,
                # no aceptar FAQ cruzado de AtenciónCliente.
                if needs_strict_rag_fallback and result.matched_category == "AtencionCliente":
                    continue
                return result

        # Solo permitir fallback global cuando NO hay categorización útil.
        # Evita falsos positivos cross-category (ej: investigación -> FAQ ubicación).
        has_specific_categories = any(cat != "Otro" for cat in normalized_categories)
        if not has_specific_categories:
            for category in self.faq_files.keys():
                if category in checked:
                    continue
                result = self._search_in_category(question, category)
                if result and result.found:
                    return result

        return FAQAgentResult(found=False)
