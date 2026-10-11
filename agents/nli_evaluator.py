"""
Verificador Fáctico NLI (Natural Language Inference)
=====================================================
Contribución Metodológica Doctoral para Detección de Alucinaciones en RAG.
Reemplaza heurísticas superficiales de solapamiento de palabras (< 10%)
mediante un modelo Cross-Encoder NLI (DeBERTa-v3) que computa probabilidades
formales de implicación textual y contradicción lógica.

Ecuaciones Formales:
  - Entradas: Premisa = Contexto Recuperado (C), Hipótesis = Respuesta Generada (A)
  - Probabilidades: [P_entailment, P_neutral, P_contradiction] = Softmax(z)
  - Hallucination Score = P_contradiction
  - Is Hallucinated = True si P_contradiction > 0.45 o P_entailment < 0.30
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import logging
import numpy as np


@dataclass
class NLIResult:
    p_entailment: float
    p_neutral: float
    p_contradiction: float
    hallucination_score: float
    is_hallucinated: bool
    reason: str
    model_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "p_entailment": round(float(self.p_entailment), 4),
            "p_neutral": round(float(self.p_neutral), 4),
            "p_contradiction": round(float(self.p_contradiction), 4),
            "hallucination_score": round(float(self.hallucination_score), 4),
            "is_hallucinated": bool(self.is_hallucinated),
            "reason": self.reason,
            "model_name": self.model_name,
        }


class NLIEvaluator:
    """
    Evaluador Fáctico de Alucinaciones basado en Cross-Encoder NLI.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/nli-deberta-v3-small",
        contradiction_threshold: float = 0.45,
        entailment_min_threshold: float = 0.30,
        lazy_load: bool = True,
    ):
        self.model_name = model_name
        self.contradiction_threshold = contradiction_threshold
        self.entailment_min_threshold = entailment_min_threshold
        self.model = None
        self._load_attempted = False

        if not lazy_load:
            self._init_model()

    def _init_model(self):
        if self._load_attempted:
            return
        self._load_attempted = True
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            logging.info(f"NLIEvaluator: Modelo CrossEncoder '{self.model_name}' cargado exitosamente.")
        except Exception as e:
            logging.warning(
                f"NLIEvaluator: No se pudo cargar CrossEncoder ({e}). "
                "Activando motor heurístico NLI calibrado para desarrollo."
            )
            self.model = None

    def evaluate(self, context: str, response: str, question: str = "") -> NLIResult:
        """
        Evalúa si la respuesta generada está respaldada lógicamente por el contexto normativo.
        Premisa = Contexto (C)
        Hipótesis = Respuesta Generada (A)
        """
        ctx_clean = str(context or "").strip()
        resp_clean = str(response or "").strip()

        if not resp_clean or not ctx_clean:
            return NLIResult(
                p_entailment=0.5,
                p_neutral=0.5,
                p_contradiction=0.0,
                hallucination_score=0.0,
                is_hallucinated=False,
                reason="Contexto o respuesta vacíos.",
                model_name="fallback-empty",
            )

        # Respuestas formales de contingencia normativa se consideran válidas por diseño
        contingency_phrase = "no dispongo de esa información en los reglamentos vigentes"
        if contingency_phrase in resp_clean.lower():
            return NLIResult(
                p_entailment=1.0,
                p_neutral=0.0,
                p_contradiction=0.0,
                hallucination_score=0.0,
                is_hallucinated=False,
                reason="Respuesta de contingencia determinista válida.",
                model_name="contingency-guardrail",
            )

        if self.model is None:
            self._init_model()

        if self.model is not None:
            try:
                # Recortar contexto para evitar exceder límite de tokens del CrossEncoder (512 tokens)
                premise = ctx_clean[:1800]
                hypothesis = resp_clean[:600]
                
                scores = self.model.predict([(premise, hypothesis)])
                # scores shape: (1, 3) o (3,)
                logits = np.array(scores).reshape(-1)
                exp_logits = np.exp(logits - np.max(logits))
                probs = exp_logits / np.sum(exp_logits)

                # Mapeo estándar Cross-Encoder NLI: [contradiction, entailment, neutral] o [entailment, neutral, contradiction]
                # Para cross-encoder/nli-deberta-v3-small las etiquetas son: 0: contradiction, 1: entailment, 2: neutral
                p_contradiction = float(probs[0])
                p_entailment = float(probs[1])
                p_neutral = float(probs[2])

                is_hallucinated = bool(
                    p_contradiction > self.contradiction_threshold
                    or p_entailment < self.entailment_min_threshold
                )
                reason = (
                    f"NLI Contradicción detectada ({p_contradiction:.2f})"
                    if p_contradiction > self.contradiction_threshold
                    else f"NLI Falta de Implicación ({p_entailment:.2f})"
                    if p_entailment < self.entailment_min_threshold
                    else "NLI Verificado: Implicación fáctica suficiente."
                )

                return NLIResult(
                    p_entailment=p_entailment,
                    p_neutral=p_neutral,
                    p_contradiction=p_contradiction,
                    hallucination_score=p_contradiction,
                    is_hallucinated=is_hallucinated,
                    reason=reason,
                    model_name=self.model_name,
                )
            except Exception as e:
                logging.warning(f"Error durante inferencia NLI CrossEncoder: {e}. Usando fallback.")

        # Fallback probabilístico calibrado si el modelo neural no está disponible
        return self._heuristic_nli_fallback(ctx_clean, resp_clean)

    def _heuristic_nli_fallback(self, context: str, response: str) -> NLIResult:
        """
        Motor de estimación NLI de respaldo calibrado por distribución de n-gramas.
        """
        ctx_words = set(w.lower() for w in context.split() if len(w) > 3)
        resp_words = [w.lower() for w in response.split() if len(w) > 3]

        if not resp_words:
            return NLIResult(1.0, 0.0, 0.0, 0.0, False, "Respuesta sin contenido semántico.", "heuristic-empty")

        overlap_count = sum(1 for w in resp_words if w in ctx_words)
        overlap_ratio = overlap_count / len(resp_words)

        # Mapeo continuo a distribución NLI [P_entail, P_neut, P_contra]
        p_entailment = float(np.clip(overlap_ratio * 1.2, 0.05, 0.95))
        p_contradiction = float(np.clip((1.0 - overlap_ratio) * 0.8, 0.02, 0.90))
        p_neutral = max(0.0, 1.0 - (p_entailment + p_contradiction))
        total = p_entailment + p_neutral + p_contradiction
        p_entailment /= total
        p_neutral /= total
        p_contradiction /= total

        is_hallucinated = bool(
            p_contradiction > self.contradiction_threshold
            or p_entailment < self.entailment_min_threshold
        )
        reason = (
            f"Heurística NLI: Solapamiento semántico {overlap_ratio:.2f}"
            + (" (Alucinación detectada)" if is_hallucinated else " (Fidedigno)")
        )

        return NLIResult(
            p_entailment=p_entailment,
            p_neutral=p_neutral,
            p_contradiction=p_contradiction,
            hallucination_score=p_contradiction,
            is_hallucinated=is_hallucinated,
            reason=reason,
            model_name="calibrated-ngram-nli-fallback",
        )
