"""
Algoritmo DACT (Dynamic Adaptive Cascade Thresholding)
======================================================
Contribución Algorítmica Doctoral para Enrutamiento Adaptativo por Incertidumbre.
Reemplaza umbrales estáticos fijos (θ = 0.75) mediante el análisis de la distribución
de similitudes del top-k en FAISS, calculando entropía normalizada de Shannon y margen semántico.

Ecuaciones Formales:
  1. Margen Semántico: Δ₁,₂ = s₁ - s₂
  2. Distribución Softmax con Temperatura: p_i = exp(s_i / τ) / Σ exp(s_j / τ)
  3. Entropía Normalizada: H(S_k) = - (1 / log₂(k)) * Σ p_i * log₂(p_i + ε)
  4. Umbral Dinámico: θ_dynamic = clip(θ_base + α * H(S_k) - β * Δ₁,₂, θ_min, θ_max)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
import math
import numpy as np


@dataclass
class DACTResult:
    s1: float
    s2: float
    delta_margin: float
    normalized_entropy: float
    theta_dynamic: float
    should_serve_faq: bool
    probabilities: List[float] = field(default_factory=list)
    top_k_scores: List[float] = field(default_factory=list)
    decision: str = "FALLBACK_RAG"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "s1": round(float(self.s1), 4),
            "s2": round(float(self.s2), 4),
            "delta_margin": round(float(self.delta_margin), 4),
            "normalized_entropy": round(float(self.normalized_entropy), 4),
            "theta_dynamic": round(float(self.theta_dynamic), 4),
            "should_serve_faq": bool(self.should_serve_faq),
            "decision": self.decision,
            "probabilities": [round(float(p), 4) for p in self.probabilities],
        }


class DACTRouter:
    """
    Enrutador Adaptativo Dinámico basado en Entropía e Incertidumbre.
    """

    def __init__(
        self,
        theta_base: float = 0.75,
        alpha: float = 0.15,
        beta: float = 0.20,
        theta_min: float = 0.60,
        theta_max: float = 0.88,
        tau: float = 0.10,
        epsilon: float = 1e-12,
    ):
        self.theta_base = float(theta_base)
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.theta_min = float(theta_min)
        self.theta_max = float(theta_max)
        self.tau = float(tau)
        self.epsilon = float(epsilon)

    def compute_threshold(self, scores: List[float], k: int = 3) -> DACTResult:
        """
        Calcula el umbral dinámico a partir de la lista de similitudes coseno del top-k.
        Scores debe estar ordenado descendentemente: s1 >= s2 >= ... >= sk.
        """
        if not scores:
            return DACTResult(
                s1=0.0,
                s2=0.0,
                delta_margin=0.0,
                normalized_entropy=1.0,
                theta_dynamic=self.theta_max,
                should_serve_faq=False,
                decision="FALLBACK_NO_SCORES",
            )

        # Truncar o padear hasta k candidatos
        k_eff = max(2, min(k, len(scores)))
        s_arr = np.array(scores[:k_eff], dtype=np.float64)

        s1 = float(s_arr[0])
        s2 = float(s_arr[1]) if len(s_arr) > 1 else 0.0

        # 1. Margen de confianza semántica
        delta_1_2 = s1 - s2

        # 2. Distribución Softmax con temperatura tau
        # Restamos max(s_arr) por estabilidad numérica
        exp_scaled = np.exp((s_arr - np.max(s_arr)) / self.tau)
        denom = np.sum(exp_scaled)
        probabilities = exp_scaled / (denom + self.epsilon)

        # 3. Entropía Normalizada de Shannon
        # H(S_k) = - (1 / log2(k_eff)) * sum(p_i * log2(p_i + eps))
        log_probs = np.log2(probabilities + self.epsilon)
        entropy_raw = -np.sum(probabilities * log_probs)
        max_entropy = math.log2(k_eff) if k_eff > 1 else 1.0
        normalized_entropy = float(entropy_raw / (max_entropy + self.epsilon))
        normalized_entropy = max(0.0, min(1.0, normalized_entropy))

        # 4. Umbral Dinámico DACT
        # theta_dynamic = clip(theta_base + alpha * H - beta * delta, theta_min, theta_max)
        theta_calc = self.theta_base + (self.alpha * normalized_entropy) - (self.beta * delta_1_2)
        theta_dynamic = float(np.clip(theta_calc, self.theta_min, self.theta_max))

        # Regla de Decisión Doctoral
        should_serve_faq = bool(s1 >= theta_dynamic)
        decision = "FAQ_ACCEPTED" if should_serve_faq else "FALLBACK_RAG"

        return DACTResult(
            s1=s1,
            s2=s2,
            delta_margin=delta_1_2,
            normalized_entropy=normalized_entropy,
            theta_dynamic=theta_dynamic,
            should_serve_faq=should_serve_faq,
            probabilities=probabilities.tolist(),
            top_k_scores=s_arr.tolist(),
            decision=decision,
        )
