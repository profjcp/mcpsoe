import unittest
import os
import json
import tempfile
import shutil

from continual_learning.doctoral_evaluator import DoctoralEvaluator, ConditionMetrics, StatisticalComparison


class TestDoctoralEvaluator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.report_path = os.path.join(self.test_dir, "test_report.md")
        self.evaluator = DoctoralEvaluator(significance_alpha=0.05)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_mcnemar_identical_outcomes(self):
        outcomes_a = [1, 1, 0, 1, 0]
        outcomes_b = [1, 1, 0, 1, 0]
        chi2, p_val, is_sig = self.evaluator.compute_mcnemar_test(outcomes_a, outcomes_b)
        self.assertEqual(chi2, 0.0)
        self.assertEqual(p_val, 1.0)
        self.assertFalse(is_sig)

    def test_mcnemar_significant_improvement(self):
        # A tiene 40 fallos de 100, B tiene solo 2 fallos de 100
        outcomes_a = [1] * 60 + [0] * 40
        outcomes_b = [1] * 98 + [0] * 2
        chi2, p_val, is_sig = self.evaluator.compute_mcnemar_test(outcomes_a, outcomes_b)
        self.assertGreater(chi2, 20.0)
        self.assertLess(p_val, 0.001)
        self.assertTrue(is_sig)

    def test_mann_whitney_test(self):
        # Distribución lenta vs rápida
        latencies_slow = [30.0, 35.5, 42.1, 28.9, 33.4, 45.0, 38.0, 29.5]
        latencies_fast = [2.8, 3.1, 2.5, 3.4, 4.0, 2.9, 3.2, 3.0]
        u_stat, p_val, is_sig = self.evaluator.compute_mann_whitney_test(latencies_slow, latencies_fast)
        self.assertLess(p_val, 0.001)
        self.assertTrue(is_sig)

    def test_evaluate_experimental_battery_and_report_generation(self):
        # Simular 20 preguntas con diferentes clasificaciones
        mock_resultados = []
        for i in range(20):
            is_bad = i in [2, 5, 8, 11]  # 4 fallos en C0
            mock_resultados.append({
                "question": f"Pregunta {i}",
                "response": f"Respuesta normativa {i} [Reglamento, Art. {i}]" if not is_bad else "Alucinación libre",
                "clasificacion": "posible_alucinacion" if is_bad else "correcta",
                "total_s": 35.0 if is_bad else 25.0,
                "ttft_s": 8.0,
                "source": "FAQ" if (i % 4 == 0) else "RAG_DOC",
                "nli_audit": {
                    "is_hallucinated": is_bad,
                    "p_contradiction": 0.85 if is_bad else 0.05,
                    "p_entailment": 0.10 if is_bad else 0.90
                }
            })

        results = self.evaluator.evaluate_experimental_battery(mock_resultados)
        self.assertIn("conditions", results)
        self.assertIn("C0", results["conditions"])
        self.assertIn("C1", results["conditions"])
        self.assertIn("C2", results["conditions"])

        c0 = results["conditions"]["C0"]
        c1 = results["conditions"]["C1"]
        c2 = results["conditions"]["C2"]

        # Verificar mejora progresiva
        self.assertGreater(c0["ahr"], c1["ahr"])
        self.assertGreater(c1["ahr"], c2["ahr"])
        self.assertGreater(c0["avg_latency_s"], c2["avg_latency_s"])
        self.assertGreater(c2["ccr"], c0["ccr"])

        # Generar reporte
        report_content = self.evaluator.generate_doctoral_markdown_report(results, output_path=self.report_path)
        self.assertTrue(os.path.exists(self.report_path))
        self.assertIn("Closed-Loop Observability-Driven Adaptive RAG", report_content)
        self.assertIn("Prueba de McNemar", report_content)
        self.assertIn("Mann-Whitney", report_content)
        self.assertIn("APROBADO CON DISTINCIÓN", report_content)


if __name__ == "__main__":
    unittest.main()
