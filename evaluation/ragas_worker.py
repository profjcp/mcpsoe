"""
RAGAs Worker - Evaluación de métricas RAG para SoeBOT
"""
import json
import os
import re
import unicodedata
import requests
from typing import Dict, Any, List, Optional


class RAGAsWorker:
    """Worker para calcular métricas RAGAs sobre endpoint /ask en streaming."""

    def __init__(
        self,
        base_url: str = "http://localhost:9000",
        interaction_log_path: str = "interaction_logs.jsonl",
        user_id: str = "eval_ragas",
    ):
        self.base_url = base_url.rstrip("/")
        self.interaction_log_path = interaction_log_path
        self.user_id = user_id

    def _normalize(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _tokenize(self, text: str) -> List[str]:
        normalized = self._normalize(text)
        return [tok for tok in normalized.split(" ") if tok]

    def _read_jsonl(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    def _find_latest_interaction(self, question: str) -> Optional[Dict[str, Any]]:
        normalized_q = self._normalize(question)
        records = self._read_jsonl(self.interaction_log_path)
        for rec in reversed(records):
            rec_user = str(rec.get("user_id", ""))
            rec_q = self._normalize(str(rec.get("question", "")))
            if rec_user == self.user_id and rec_q == normalized_q:
                return rec
        return None

    def ask(self, question: str) -> Dict[str, Any]:
        """Envía pregunta por /ask streaming y reconstruye la respuesta."""
        response = requests.post(
            f"{self.base_url}/ask",
            json={"question": question, "user_id": self.user_id},
            timeout=60,
            stream=True,
        )
        response.raise_for_status()

        chunks: List[str] = []
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                chunks.append(chunk.decode("utf-8", errors="ignore"))
        answer = "".join(chunks).strip()

        interaction = self._find_latest_interaction(question) or {}
        source = str(interaction.get("source", "UNKNOWN")).upper()

        # Normalización para evaluación tipo-dataset vs tipo-runtime
        canonical_map = {
            "GUIDANCE": "GUIDANCE",
            "FAQ": "FAQ",
            "CACHE": "FAQ",      # cache de respuestas válidas FAQ/RAG
            "RAG_DOC": "RAG",
            "GRAPH_RAG": "RAG",
            "RAG": "RAG",
            "UNKNOWN": "UNKNOWN",
        }
        canonical_type = canonical_map.get(source, source)

        return {
            "answer": answer,
            "actual_type": source,
            "actual_type_canonical": canonical_type,
            "context": interaction.get("response_text", ""),
            "sources": interaction.get("sources", []),
            "routing_trace": interaction.get("routing_trace", {}),
        }

    def calculate_faithfulness(self, answer: str, context: str) -> float:
        """Aproximación simple de Faithfulness por solapamiento léxico."""
        answer_tokens = set(self._tokenize(answer))
        context_tokens = set(self._tokenize(context))
        if not answer_tokens or not context_tokens:
            return 0.0
        overlap = len(answer_tokens.intersection(context_tokens))
        return min(overlap / max(1, len(answer_tokens)), 1.0)

    def calculate_answer_relevancy(self, question: str, answer: str) -> float:
        """Aproximación simple de relevancia pregunta-respuesta."""
        q_tokens = set(self._tokenize(question))
        a_tokens = set(self._tokenize(answer))
        if not q_tokens or not a_tokens:
            return 0.0
        overlap = len(q_tokens.intersection(a_tokens))
        return min(overlap / max(1, len(q_tokens)), 1.0)

    def calculate_context_precision(self, context: str, answer: str) -> float:
        """Aproximación de precision de contexto por uso de chunks no vacíos."""
        if not context.strip() or not answer.strip():
            return 0.0
        chunks = [c.strip() for c in context.split("---") if c.strip()]
        if not chunks:
            return 0.0
        useful = 0
        answer_tokens = set(self._tokenize(answer))
        for c in chunks:
            c_tokens = set(self._tokenize(c))
            if answer_tokens.intersection(c_tokens):
                useful += 1
        return useful / max(1, len(chunks))

    def evaluate_case(self, question: str, expected_type: str) -> Dict[str, Any]:
        """Evalúa un caso individual."""
        try:
            result = self.ask(question)
            answer = result.get("answer", "")
            context = result.get("context", "")
            actual_type = str(result.get("actual_type", "UNKNOWN")).upper()
            actual_type_canonical = str(result.get("actual_type_canonical", "UNKNOWN")).upper()

            return {
                "question": question,
                "expected_type": str(expected_type).upper(),
                "actual_type": actual_type,
                "actual_type_canonical": actual_type_canonical,
                "answer_preview": answer[:300],
                "faithfulness": self.calculate_faithfulness(answer, context),
                "answer_relevancy": self.calculate_answer_relevancy(question, answer),
                "context_precision": self.calculate_context_precision(context, answer),
                "success": True,
                "sources_count": len(result.get("sources", []) or []),
                "routing_trace": result.get("routing_trace", {}),
            }
        except Exception as e:
            return {
                "question": question,
                "expected_type": str(expected_type).upper(),
                "actual_type": "ERROR",
                "success": False,
                "error": str(e),
            }


if __name__ == "__main__":
    worker = RAGAsWorker()
    test_question = "¿Cuál es el costo de la maestría?"
    result = worker.evaluate_case(test_question, "FAQ")
    print(json.dumps(result, indent=2, ensure_ascii=False))
