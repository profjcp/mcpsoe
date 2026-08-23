import os
import sys
import unittest
import numpy as np

# Añadir directorio raíz al PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrieval.hybrid_retriever import HybridRetriever, tokenize_spanish
from agents.hallucination_grader import HallucinationGrader
from agents.query_rewriter import QueryRewriter


class DummyFAISS:
    def search(self, q_np, k):
        # Devuelve índices mock
        indices = np.array([[0, 1]], dtype=int)
        distances = np.array([[0.1, 0.5]], dtype=float)
        return distances, indices


class TestRAGImplementation(unittest.TestCase):

    def setUp(self):
        self.dummy_faiss = DummyFAISS()
        self.sample_chunks = [
            {
                "text": "El costo de la matrícula para la Maestría en Ciberseguridad es de 500 USD.",
                "metadata": {
                    "doc_id": "faq_atencion_cliente.txt",
                    "titulo": "FAQ Atención al Cliente",
                    "categoria": "AtencionCliente",
                    "nivel_acceso": "publico",
                    "articulo": "Sección 1"
                }
            },
            {
                "text": "Para defender la tesis de posgrado se requiere haber aprobado 16 módulos académicos.",
                "metadata": {
                    "doc_id": "faq_academica.txt",
                    "titulo": "Reglamento Académico",
                    "categoria": "Academica",
                    "nivel_acceso": "estudiante",
                    "articulo": "Reglamento General, Art. 45"
                }
            }
        ]
        self.dummy_embed_fn = lambda q: [0.1] * 768

    def test_tokenize_spanish(self):
        tokens = tokenize_spanish("¿Cuál es el costo de la matrícula?")
        self.assertIn("costo", tokens)
        self.assertIn("matrícula", tokens)

    def test_hybrid_retriever_access_control(self):
        retriever = HybridRetriever(
            faiss_index=self.dummy_faiss,
            chunks=self.sample_chunks,
            embed_query_fn=self.dummy_embed_fn,
            top_k=2
        )

        # Usuario 'publico' sólo debe poder ver el chunk de nivel 'publico'
        public_results, _, metrics = retriever.search("costo matrícula", user_access_level="publico")
        self.assertGreaterEqual(len(public_results), 1)
        self.assertIn("mean_rrf_score", metrics)
        self.assertIn("dual_hits_count", metrics)
        self.assertIn("blocked_chunks_count", metrics)

        for res in public_results:
            self.assertEqual(res["metadata"]["nivel_acceso"], "publico")

        # Usuario 'estudiante' debe poder ver chunks de nivel 'publico' y 'estudiante'
        student_results, _, student_metrics = retriever.search("defensa tesis", user_access_level="estudiante")
        self.assertGreaterEqual(len(student_results), 1)

    def test_hallucination_grader_fallback(self):
        grader = HallucinationGrader(llm=None)
        context = "El costo de la matrícula es de 500 USD."
        grounded_resp = "El costo de la matrícula asciende a 500 USD."
        is_grounded, reason = grader.grade(context, grounded_resp)
        self.assertTrue(is_grounded)

    def test_query_rewriter_fallback(self):
        rewriter = QueryRewriter(llm=None)
        rewritten = rewriter.rewrite("cuáles son los módulos", categories=["Academica"])
        self.assertIn("módulos", rewritten)
        self.assertIn("programa", rewritten)


if __name__ == "__main__":
    unittest.main()
