import unittest
import os
import sys

# Asegurar importación de módulos raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import tempfile
import shutil
import time

from continual_learning.drift_detector import DriftThresholds, DriftDetector, TriggerEvent


class TestDriftDetector(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.interactions_file = os.path.join(self.test_dir, "interactions.jsonl")
        self.feedback_file = os.path.join(self.test_dir, "feedback.jsonl")
        self.events_file = os.path.join(self.test_dir, "drift_events.jsonl")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_insufficient_samples_does_not_trigger(self):
        thresholds = DriftThresholds(window_size=20, min_samples_to_evaluate=10)
        detector = DriftDetector(
            thresholds=thresholds,
            interaction_log_path=self.interactions_file,
            events_log_path=self.events_file
        )

        # Solo 5 muestras (menos que el mínimo de 10)
        for i in range(5):
            res = detector.record_interaction({
                "question": f"Pregunta {i}",
                "hallucinated": True
            })
            self.assertIsNone(res)

        metrics = detector.evaluate_window()
        self.assertFalse(metrics.has_drift)
        self.assertIn("insuficientes", metrics.drift_reasons[0].lower())

    def test_condition1_ahr_threshold_trigger(self):
        """
        Verifica que AHR > 15% active la señal de reentrenamiento.
        """
        thresholds = DriftThresholds(
            window_size=10,
            min_samples_to_evaluate=5,
            max_ahr_threshold=0.15,
            cooldown_seconds=1.0
        )
        triggered_events = []

        detector = DriftDetector(
            thresholds=thresholds,
            interaction_log_path=self.interactions_file,
            events_log_path=self.events_file,
            on_trigger_callback=lambda evt: triggered_events.append(evt)
        )

        # Enviar 10 interacciones, con 3 alucinaciones (30% > 15%)
        for i in range(10):
            is_bad = i in [2, 4, 7]
            detector.record_interaction({
                "question": f"Pregunta {i}",
                "hallucinated": is_bad,
                "routing_trace": {
                    "nli_audit": {
                        "is_hallucinated": is_bad,
                        "p_contradiction": 0.82 if is_bad else 0.05
                    }
                }
            })

        metrics = detector.evaluate_window()
        self.assertTrue(metrics.has_drift)
        self.assertGreater(metrics.ahr_rate, 0.15)
        self.assertTrue(any("AHR_EXCEEDED" in r for r in metrics.drift_reasons))

        # Dar breve tiempo para el hilo asíncrono
        time.sleep(0.1)
        self.assertGreater(len(triggered_events), 0)
        self.assertTrue(os.path.exists(self.events_file))

    def test_contingency_fallback_does_not_count_as_hallucination(self):
        """
        La frase de contingencia formal es honesta (abierto fáctico), por lo que no es alucinación.
        """
        thresholds = DriftThresholds(window_size=10, min_samples_to_evaluate=5, max_ahr_threshold=0.15)
        detector = DriftDetector(thresholds=thresholds, events_log_path=self.events_file)

        for i in range(10):
            detector.record_interaction({
                "question": f"Pregunta vacía {i}",
                "is_contingency_fallback": True,
                "hallucinated": False,
                "routing_trace": {
                    "nli_audit": {"is_hallucinated": False, "p_contradiction": 0.0}
                }
            })

        metrics = detector.evaluate_window()
        self.assertFalse(metrics.has_drift)
        self.assertEqual(metrics.ahr_rate, 0.0)

    def test_condition2_satisfaction_degradation_trigger(self):
        """
        Verifica que calificación Likert media < 3.2 active la señal.
        """
        thresholds = DriftThresholds(
            window_size=10,
            min_samples_to_evaluate=5,
            min_satisfaction_threshold=3.2,
            cooldown_seconds=1.0
        )
        detector = DriftDetector(thresholds=thresholds, events_log_path=self.events_file)

        # 6 interacciones normales
        for i in range(6):
            detector.record_interaction({"question": f"Q{i}", "hallucinated": False})

        # Feedbacks bajos (1 y 2 estrellas -> promedio 1.67 < 3.2)
        for val in [2, 1, 2]:
            detector.record_feedback({"satisfaction": val})

        metrics = detector.evaluate_window()
        self.assertTrue(metrics.has_drift)
        self.assertIsNotNone(metrics.avg_satisfaction)
        self.assertLess(metrics.avg_satisfaction, 3.2)
        self.assertTrue(any("SATISFACTION_DEGRADED" in r for r in metrics.drift_reasons))

    def test_condition3_dact_entropy_trigger(self):
        """
        Verifica que entropía sostenida H(Sk) > 0.65 active la señal.
        """
        thresholds = DriftThresholds(
            window_size=10,
            min_samples_to_evaluate=5,
            max_dact_entropy_threshold=0.65,
            cooldown_seconds=1.0
        )
        detector = DriftDetector(thresholds=thresholds, events_log_path=self.events_file)

        # 8 consultas con alta incertidumbre (ambigüedad en las categorías DACT)
        for i in range(8):
            detector.record_interaction({
                "question": f"Pregunta ambigua {i}",
                "hallucinated": False,
                "routing_trace": {
                    "dact_metrics": {"normalized_entropy": 0.85}
                }
            })

        metrics = detector.evaluate_window()
        self.assertTrue(metrics.has_drift)
        self.assertGreater(metrics.avg_dact_entropy, 0.65)
        self.assertTrue(any("DACT_ENTROPY_HIGH" in r for r in metrics.drift_reasons))

    def test_cooldown_prevents_trigger_flood(self):
        """
        Verifica que no se emitan múltiples disparos durante el tiempo de enfriamiento.
        """
        thresholds = DriftThresholds(
            window_size=10,
            min_samples_to_evaluate=5,
            max_ahr_threshold=0.10,
            cooldown_seconds=50.0  # Cooldown largo
        )
        dispatched_count = [0]
        detector = DriftDetector(
            thresholds=thresholds,
            events_log_path=self.events_file,
            on_trigger_callback=lambda evt: dispatched_count.__setitem__(0, dispatched_count[0] + 1)
        )

        for i in range(8):
            detector.record_interaction({"question": f"Q{i}", "hallucinated": True})

        # Primer disparo ejecutado
        self.assertEqual(detector.total_triggers, 1)

        # Entran 5 más con fallos pero dentro de cooldown -> NO debe disparar otro evento
        for j in range(5):
            res = detector.record_interaction({"question": f"Extra {j}", "hallucinated": True})
            self.assertIsNone(res)

        self.assertEqual(detector.total_triggers, 1)

    def test_sync_from_logs(self):
        """Verifica la carga y evaluación directa desde archivos de logs."""
        # Escribir 6 registros con 2 alucinaciones en el archivo
        with open(self.interactions_file, "w", encoding="utf-8") as f:
            for i in range(6):
                f.write(json.dumps({
                    "question": f"Test {i}",
                    "hallucinated": i in [1, 3]
                }) + "\n")

        with open(self.feedback_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"satisfaction": 4}) + "\n")

        detector = DriftDetector(
            thresholds=DriftThresholds(window_size=10, min_samples_to_evaluate=5, max_ahr_threshold=0.20),
            interaction_log_path=self.interactions_file,
            feedback_log_path=self.feedback_file,
            events_log_path=self.events_file
        )
        metrics = detector.sync_from_logs()
        self.assertEqual(metrics.window_count, 6)
        self.assertAlmostEqual(metrics.ahr_rate, 2 / 6, places=2)
        self.assertEqual(metrics.avg_satisfaction, 4.0)


if __name__ == "__main__":
    unittest.main()
