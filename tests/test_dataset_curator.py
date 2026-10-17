import unittest
import os
import json
import tempfile
import shutil

from continual_learning.dataset_curator import DatasetCurator, DPOTriplet, SFTExample


class TestDatasetCurator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.curator = DatasetCurator(min_text_len=10)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_text_cleaning_and_prompt_formatting(self):
        q = "  ¿Cómo tramitar monografía? \r\n\n\n "
        ctx = " [Reglamento, Art. 5] La monografía debe enviarse por correo. "
        prompt = self.curator.format_prompt(q, ctx)
        self.assertIn("<context>", prompt)
        self.assertIn("<question>", prompt)
        self.assertIn("¿Cómo tramitar monografía?", prompt)
        self.assertIn("[Reglamento, Art. 5]", prompt)

    def test_mine_mock_simulation_results(self):
        mock_sim_path = os.path.join(self.test_dir, "mock_sim.json")
        mock_data = {
            "total": 2,
            "resultados": [
                {
                    "question": "¿Dónde tramito el título?",
                    "response": "Puede ir a la oficina del tercer piso cualquier día sin cita.",
                    "expected_answer": "Debe agendar cita en ventanilla única.",
                    "clasificacion": "posible_alucinacion",
                    "user_role": "Estudiante",
                    "area": "AtencionCliente",
                },
                {
                    "question": "¿Quién es el coordinador?",
                    "response": "El coordinador es el Dr. Juan Pérez [Facultad, Art. 2].",
                    "expected_answer": "El Dr. Juan Pérez",
                    "clasificacion": "correcta",
                    "user_role": "Estudiante",
                    "area": "Academica",
                }
            ]
        }
        with open(mock_sim_path, "w", encoding="utf-8") as f:
            json.dump(mock_data, f)

        count = self.curator.mine_from_simulation_results(mock_sim_path)
        self.assertEqual(count, 1)
        self.assertEqual(len(self.curator.dpo_pairs), 1)
        self.assertEqual(len(self.curator.sft_examples), 1)

        dpo = self.curator.dpo_pairs[0]
        self.assertIn("cita en ventanilla", dpo.chosen)
        self.assertIn("tercer piso", dpo.rejected)
        self.assertIn("mock_sim.json", dpo.metadata["source_file"])

    def test_mine_mock_interaction_logs(self):
        mock_log_path = os.path.join(self.test_dir, "mock_logs.jsonl")
        log_entry = {
            "timestamp": "2026-10-13T10:00:00",
            "user_id": "test_user_01",
            "question": "¿Cuántas materias puedo convalidar?",
            "response_text": "Puedes convalidar hasta 10 materias sin límite de tiempo.",
            "hallucinated": True,
            "routing_trace": {
                "nli_audit": {
                    "is_hallucinated": True,
                    "p_contradiction": 0.88,
                }
            },
            "sources": [
                {
                    "title": "Reglamento de Convalidaciones",
                    "section": "Art. 12",
                    "snippet": "Se permite un máximo de 3 materias aprobadas en los últimos 2 años."
                }
            ]
        }
        with open(mock_log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        count = self.curator.mine_from_interaction_logs(mock_log_path)
        self.assertEqual(count, 1)
        self.assertEqual(len(self.curator.dpo_pairs), 1)

        dpo = self.curator.dpo_pairs[0]
        self.assertIn("máximo de 3 materias", dpo.chosen)
        self.assertIn("hasta 10 materias", dpo.rejected)
        self.assertEqual(dpo.metadata["p_contradiction"], 0.88)

    def test_export_datasets(self):
        dpo_item = DPOTriplet(
            id="test_01",
            prompt="<question>¿Test?</question>",
            chosen="Respuesta correcta [Doc, Art]",
            rejected="Respuesta inventada"
        )
        self.curator.dpo_pairs.append(dpo_item)
        dpo_path, sft_path = self.curator.export_datasets(self.test_dir)

        self.assertTrue(os.path.exists(dpo_path))
        self.assertTrue(os.path.exists(sft_path))

        with open(dpo_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["id"], "test_01")
            self.assertEqual(parsed["chosen"], "Respuesta correcta [Doc, Art]")

    def test_mine_real_resultados_100(self):
        real_file = "simulation_results/resultados_100.json"
        if os.path.exists(real_file):
            curator_real = DatasetCurator()
            count = curator_real.mine_from_simulation_results(real_file)
            self.assertGreater(count, 0)
            summary = curator_real.get_summary()
            self.assertGreater(summary["total_dpo_pairs"], 0)
            print(f"\n[Test Real]: Extraídos {summary['total_dpo_pairs']} pares DPO reales de resultados_100.json")


if __name__ == "__main__":
    unittest.main()
