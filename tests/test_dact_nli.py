import unittest
import numpy as np

from retrieval.dact import DACTRouter, DACTResult
from agents.nli_evaluator import NLIEvaluator, NLIResult
from agents.faq_agent import FAQAgent, FAQAgentResult


class TestDACTRouter(unittest.TestCase):

    def setUp(self):
        self.router = DACTRouter(
            theta_base=0.75,
            alpha=0.15,
            beta=0.20,
            theta_min=0.60,
            theta_max=0.88,
            tau=0.10,
        )

    def test_clear_winner_relaxes_threshold(self):
        # Caso claro: s1 muy superior a s2
        scores = [0.85, 0.40, 0.35]
        res = self.router.compute_threshold(scores, k=3)
        self.assertTrue(res.should_serve_faq)
        self.assertGreater(res.delta_margin, 0.4)
        # El umbral dinámico debe ser menor o igual que theta_base debido al gran margen
        self.assertLessEqual(res.theta_dynamic, 0.75)
        self.assertEqual(res.decision, "FAQ_ACCEPTED")

    def test_ambiguous_competition_raises_threshold(self):
        # Caso ambiguo: s1 y s2 casi idénticos y bajos (alta entropía, bajo margen)
        scores = [0.72, 0.71, 0.70]
        res = self.router.compute_threshold(scores, k=3)
        self.assertFalse(res.should_serve_faq)
        self.assertAlmostEqual(res.delta_margin, 0.01, places=2)
        # La entropía normalizada debe ser alta (> 0.8)
        self.assertGreater(res.normalized_entropy, 0.8)
        # El umbral dinámico debe subir por encima de theta_base (0.75)
        self.assertGreater(res.theta_dynamic, 0.75)
        self.assertEqual(res.decision, "FALLBACK_RAG")

    def test_clipping_bounds(self):
        # Caso extremo bajo: margen masivo
        scores_extreme = [0.99, 0.01, 0.00]
        res_low = self.router.compute_threshold(scores_extreme, k=3)
        self.assertGreaterEqual(res_low.theta_dynamic, 0.60)

        # Caso extremo alto: entropía máxima
        scores_flat = [0.50, 0.50, 0.50]
        res_high = self.router.compute_threshold(scores_flat, k=3)
        self.assertLessEqual(res_high.theta_dynamic, 0.88)

    def test_feedback_penalty_raises_threshold(self):
        # Caso base sin feedback negativo
        scores = [0.80, 0.50, 0.40]
        res_clean = self.router.compute_threshold(scores, k=3, feedback_penalty=0.0)
        self.assertTrue(res_clean.should_serve_faq)

        # Mismo caso pero con alto reporte histórico de errores (feedback_penalty=0.8)
        res_penalized = self.router.compute_threshold(scores, k=3, feedback_penalty=0.8)
        self.assertGreater(res_penalized.theta_dynamic, res_clean.theta_dynamic)
        self.assertEqual(res_penalized.feedback_penalty, 0.8)


class TestNLIEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = NLIEvaluator(lazy_load=True)

    def test_contingency_fallback_is_not_hallucinated(self):
        context = "Reglamento de Posgrado de la UAGRM."
        response = "No dispongo de esa información en los reglamentos vigentes. Por favor, acude a la Jefatura Académica."
        res = self.evaluator.evaluate(context, response)
        self.assertFalse(res.is_hallucinated)
        self.assertEqual(res.p_entailment, 1.0)
        self.assertEqual(res.hallucination_score, 0.0)

    def test_grounded_response_evaluation(self):
        context = "El costo de la matrícula para la Maestría en Ciberseguridad es de 500 USD por semestre según el Artículo 15."
        response = "El costo de matrícula asciende a 500 USD por semestre [Artículo 15]."
        res = self.evaluator.evaluate(context, response)
        self.assertFalse(res.is_hallucinated)
        self.assertGreater(res.p_entailment, 0.30)

    def test_unsupported_hallucination_detection(self):
        context = "El horario de clases de posgrado es de lunes a viernes de 19:00 a 22:00 horas."
        # Respuesta inventa números de teléfono y costos no existentes
        response = "Para contactar a la universidad llame al teléfono 777-12345 o pague 5000 USD de multa de penalización."
        res = self.evaluator.evaluate(context, response)
        self.assertTrue(res.is_hallucinated)
        self.assertGreater(res.hallucination_score, 0.40)


class TestFAQAgentWithDACT(unittest.TestCase):

    def test_faq_agent_dact_integration(self):
        dummy_faqs = [
            {"pregunta": "¿Cuál es el costo del programa?", "respuesta": "El costo es 500 USD", "embedding": [0.9] * 768},
            {"pregunta": "¿Cuáles son los requisitos de admisión?", "respuesta": "Título y fotocopia", "embedding": [0.2] * 768},
        ]
        
        agent = FAQAgent(
            faq_files={"AtencionCliente": "dummy_path"},
            load_faqs_fn=lambda path, embed_fn: dummy_faqs,
            embed_query_fn=lambda q: [0.9] * 768,
            threshold=0.75,
            min_token_overlap=1,
        )

        result = agent.run("¿Cuál es el costo del programa?", ["AtencionCliente"])
        self.assertTrue(result.found)
        self.assertIn("dact_metrics", result.__dict__)
        self.assertEqual(result.dact_metrics.get("decision"), "FAQ_ACCEPTED")
        self.assertGreater(result.dact_metrics.get("s1", 0), 0.9)

    def test_faq_agent_dact_with_unmapped_category(self):
        # Consulta de área Administracion/Marketing sin archivo propio
        dummy_faqs = [
            {"pregunta": "¿Cómo tramitar certificados?", "respuesta": "Acuda a caja", "embedding": [0.85] * 768},
        ]
        agent = FAQAgent(
            faq_files={"AtencionCliente": "dummy_path"},
            load_faqs_fn=lambda path, embed_fn: dummy_faqs,
            embed_query_fn=lambda q: [0.85] * 768,
            threshold=0.75,
            min_token_overlap=1,
        )

        result = agent.run("¿Cómo tramitar certificados?", ["Administracion"])
        self.assertIsNotNone(result.dact_metrics)
        self.assertIn("theta_dynamic", result.dact_metrics)
        self.assertGreater(result.dact_metrics.get("s1", 0), 0.8)


if __name__ == "__main__":
    unittest.main()
