#!/usr/bin/env python3
"""
Detector de Deriva y Disparador Autónomo de Reentrenamiento (Drift Detector)
==========================================================================
Componente Central de la Fase 3 de CLODA-RAG (Tesis Doctoral).

Monitorea la telemetría fáctica (NLI), la incertidumbre adaptativa (DACT) y
la percepción del usuario (Likert) sobre una ventana deslizante de interacciones (W).
Al detectar degradación empírica, emite de forma asíncrona la señal TRIGGER_RETRAINING
para cerrar el bucle sin bloquear las operaciones concurrentes del servidor.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Callable
import collections
import json
import logging
import os
import threading
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@dataclass
class DriftThresholds:
    """Umbrales de activación doctoral para la detección de deriva."""
    window_size: int = 50                      # Tamaño de la ventana deslizante (W)
    min_samples_to_evaluate: int = 10          # Muestras mínimas requeridas antes de evaluar
    max_ahr_threshold: float = 0.15            # AHR > 15% (Tasa de alucinación auditada NLI)
    min_satisfaction_threshold: float = 3.2    # Rating medio Likert < 3.2 / 5.0
    max_dact_entropy_threshold: float = 0.65   # Entropía DACT normalizada media H(Sk) > 0.65
    cooldown_seconds: float = 300.0            # Enfriamiento entre reentrenamientos (5 min)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DriftMetrics:
    """Métricas consolidadas de la ventana activa."""
    window_count: int = 0
    ahr_rate: float = 0.0
    avg_satisfaction: Optional[float] = None
    satisfaction_count: int = 0
    avg_dact_entropy: float = 0.0
    dact_count: int = 0
    has_drift: bool = False
    drift_reasons: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TriggerEvent:
    """Evento auditable de activación de reentrenamiento autónomo."""
    event_id: str
    timestamp: str
    reasons: List[str]
    metrics: Dict[str, Any]
    retraining_dispatched: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DriftDetector:
    """
    Detector de deriva semántica y disparador de reentrenamiento autónomo en bucle cerrado.
    """

    def __init__(
        self,
        thresholds: Optional[DriftThresholds] = None,
        interaction_log_path: str = "interaction_logs.jsonl",
        feedback_log_path: str = "feedback.jsonl",
        events_log_path: str = "continual_learning/drift_events.jsonl",
        on_trigger_callback: Optional[Callable[[TriggerEvent], None]] = None,
    ):
        self.thresholds = thresholds or DriftThresholds()
        self.interaction_log_path = interaction_log_path
        self.feedback_log_path = feedback_log_path
        self.events_log_path = events_log_path
        self.on_trigger_callback = on_trigger_callback

        self._interactions_window: collections.deque = collections.deque(maxlen=self.thresholds.window_size)
        self._feedbacks_window: collections.deque = collections.deque(maxlen=self.thresholds.window_size)
        self._last_trigger_time: float = 0.0
        self._lock = threading.Lock()
        self._total_triggers: int = 0

    @property
    def window_size(self) -> int:
        return len(self._interactions_window)

    @property
    def total_triggers(self) -> int:
        return self._total_triggers

    def record_interaction(self, record: Dict[str, Any]) -> Optional[TriggerEvent]:
        """
        Ingresa un evento de interacción a la ventana deslizante y evalúa deriva.
        Retorna TriggerEvent si se disparó reentrenamiento, None en caso contrario.
        """
        with self._lock:
            self._interactions_window.append(record)
            metrics = self._evaluate_window_unlocked()

        if metrics.has_drift:
            return self._dispatch_trigger(metrics)
        return None

    def record_feedback(self, feedback: Dict[str, Any]) -> Optional[TriggerEvent]:
        """
        Ingresa un evento de feedback cualitativo a la ventana deslizante y evalúa deriva.
        """
        with self._lock:
            self._feedbacks_window.append(feedback)
            metrics = self._evaluate_window_unlocked()

        if metrics.has_drift:
            return self._dispatch_trigger(metrics)
        return None

    def sync_from_logs(self, max_records: Optional[int] = None) -> DriftMetrics:
        """
        Carga las interacciones y feedback más recientes desde disco para sincronizar la ventana.
        """
        limit = max_records or self.thresholds.window_size

        if os.path.exists(self.interaction_log_path):
            with open(self.interaction_log_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                for l in lines[-limit:]:
                    try:
                        self._interactions_window.append(json.loads(l))
                    except Exception:
                        pass

        if os.path.exists(self.feedback_log_path):
            with open(self.feedback_log_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                for l in lines[-limit:]:
                    try:
                        self._feedbacks_window.append(json.loads(l))
                    except Exception:
                        pass

        return self.evaluate_window()

    def evaluate_window(self) -> DriftMetrics:
        """Evalúa el estado actual de la ventana deslizante de forma hilo-segura."""
        with self._lock:
            return self._evaluate_window_unlocked()

    def _evaluate_window_unlocked(self) -> DriftMetrics:
        """Cálculo matemático de las tres condiciones doctorales sobre la ventana activa."""
        n_samples = len(self._interactions_window)
        if n_samples < self.thresholds.min_samples_to_evaluate:
            return DriftMetrics(
                window_count=n_samples,
                ahr_rate=0.0,
                avg_satisfaction=None,
                satisfaction_count=0,
                avg_dact_entropy=0.0,
                dact_count=0,
                has_drift=False,
                drift_reasons=[f"Muestras insuficientes ({n_samples}/{self.thresholds.min_samples_to_evaluate})"]
            )

        # 1. Condición 1: Tasa de Alucinación Auditada (AHR)
        hallucination_count = 0
        for item in self._interactions_window:
            is_contingency = item.get("is_contingency_fallback", False)
            if is_contingency:
                continue  # Contingencia formal no cuenta como alucinación

            # Revisar múltiples campos para robustez
            hallucinated = item.get("hallucinated", False)
            nli_audit = item.get("routing_trace", {}).get("nli_audit", {})
            if not isinstance(nli_audit, dict):
                nli_audit = {}

            nli_hallucinated = nli_audit.get("is_hallucinated", False)
            p_contra = nli_audit.get("p_contradiction", 0.0)

            if hallucinated or nli_hallucinated or p_contra > 0.45:
                hallucination_count += 1

        ahr_rate = round(hallucination_count / n_samples, 4)

        # 2. Condición 2: Satisfacción Media de Usuarios (Likert 1-5)
        satisfaction_scores: List[float] = []
        for fb in self._feedbacks_window:
            sat = fb.get("satisfaction")
            if sat is not None:
                try:
                    satisfaction_scores.append(float(sat))
                except (ValueError, TypeError):
                    pass

        avg_satisfaction = round(sum(satisfaction_scores) / len(satisfaction_scores), 3) if satisfaction_scores else None

        # 3. Condición 3: Entropía Normalizada DACT H(Sk)
        entropy_scores: List[float] = []
        for item in self._interactions_window:
            dact_meta = item.get("routing_trace", {}).get("dact_metrics", {})
            if not isinstance(dact_meta, dict):
                dact_meta = {}
            ent = dact_meta.get("normalized_entropy")
            if ent is not None:
                try:
                    entropy_scores.append(float(ent))
                except (ValueError, TypeError):
                    pass

        avg_entropy = round(sum(entropy_scores) / len(entropy_scores), 4) if entropy_scores else 0.0

        # Evaluación de Deriva
        drift_reasons: List[str] = []

        if ahr_rate > self.thresholds.max_ahr_threshold:
            drift_reasons.append(
                f"AHR_EXCEEDED: Tasa de alucinación ({ahr_rate * 100:.1f}%) supera el umbral ({self.thresholds.max_ahr_threshold * 100:.1f}%)"
            )

        if avg_satisfaction is not None and avg_satisfaction < self.thresholds.min_satisfaction_threshold:
            drift_reasons.append(
                f"SATISFACTION_DEGRADED: Rating Likert ({avg_satisfaction:.2f}) inferior al umbral ({self.thresholds.min_satisfaction_threshold:.2f})"
            )

        if entropy_scores and avg_entropy > self.thresholds.max_dact_entropy_threshold:
            drift_reasons.append(
                f"DACT_ENTROPY_HIGH: Incertidumbre ({avg_entropy:.3f}) supera el umbral sostenido ({self.thresholds.max_dact_entropy_threshold:.3f})"
            )

        has_drift = len(drift_reasons) > 0

        return DriftMetrics(
            window_count=n_samples,
            ahr_rate=ahr_rate,
            avg_satisfaction=avg_satisfaction,
            satisfaction_count=len(satisfaction_scores),
            avg_dact_entropy=avg_entropy,
            dact_count=len(entropy_scores),
            has_drift=has_drift,
            drift_reasons=drift_reasons
        )

    def _dispatch_trigger(self, metrics: DriftMetrics) -> Optional[TriggerEvent]:
        """
        Emite la señal TRIGGER_RETRAINING y ejecuta el callback de forma asíncrona
        si ha transcurrido el periodo de enfriamiento (cooldown).
        """
        now = time.time()
        if (now - self._last_trigger_time) < self.thresholds.cooldown_seconds:
            logging.info(
                f"DriftDetector: Deriva detectada pero suprimida por enfriamiento "
                f"({int(self.thresholds.cooldown_seconds - (now - self._last_trigger_time))}s restantes)."
            )
            return None

        self._last_trigger_time = now
        self._total_triggers += 1

        event_id = f"cloda_trigger_{int(now)}_{self._total_triggers:03d}"
        event = TriggerEvent(
            event_id=event_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            reasons=metrics.drift_reasons,
            metrics=metrics.to_dict(),
            retraining_dispatched=True
        )

        # Registrar evento en archivo de auditoría doctoral
        self._persist_trigger_event(event)

        logging.warning(
            f"🚨 [CLODA-RAG TRIGGER_RETRAINING] Evento {event_id}: "
            f"Señal emitida por derivas: {'; '.join(metrics.drift_reasons)}"
        )

        # Despachar callback de forma desacoplada en hilo background
        if self.on_trigger_callback:
            def _async_call():
                try:
                    self.on_trigger_callback(event)
                except Exception as e:
                    logging.error(f"DriftDetector: Error en on_trigger_callback: {e}")

            t = threading.Thread(target=_async_call, name=f"CLODA_Dispatch_{event_id}", daemon=True)
            t.start()

        return event

    def _persist_trigger_event(self, event: TriggerEvent):
        """Guarda el evento de activación para la trazabilidad experimental doctoral."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.events_log_path)), exist_ok=True)
            with open(self.events_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logging.warning(f"DriftDetector: No se pudo persistir drift_events.jsonl: {e}")

    def reset_window(self):
        """Limpia el buffer de la ventana deslizante."""
        with self._lock:
            self._interactions_window.clear()
            self._feedbacks_window.clear()


if __name__ == "__main__":
    detector = DriftDetector(DriftThresholds(window_size=10, min_samples_to_evaluate=5, max_ahr_threshold=0.15))
    print("=== Probando Detector de Deriva CLODA-RAG ===")
    for i in range(10):
        # 3 fallos en 10 interacciones = 30% AHR (> 15% umbral)
        is_bad = i in [2, 5, 8]
        detector.record_interaction({
            "id": f"q_{i}",
            "hallucinated": is_bad,
            "routing_trace": {
                "nli_audit": {"is_hallucinated": is_bad, "p_contradiction": 0.85 if is_bad else 0.05},
                "dact_metrics": {"normalized_entropy": 0.75 if is_bad else 0.20}
            }
        })
    metrics = detector.evaluate_window()
    print(f"Estado de ventana: Deriva={metrics.has_drift} | AHR={metrics.ahr_rate*100}% | H(Sk)={metrics.avg_dact_entropy}")
    print(f"Razones: {metrics.drift_reasons}")
