import unittest
import os
import sys

# Asegurar importación de módulos raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import tempfile
import shutil
import time

from continual_learning.train_worker import TrainConfig, TrainWorker, TrainingResult


class TestTrainWorker(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dataset_file = os.path.join(self.test_dir, "synthetic_dataset.jsonl")
        self.output_dir = os.path.join(self.test_dir, "adapters", "checkpoint_test")

        # Crear micro-lote sintético de 5 ejemplos normativos
        examples = [
            {
                "prompt": "<question>¿Cuántas materias puedo reprobar?</question>",
                "chosen": "Puede reprobar como máximo 2 materias según [Reglamento, Art. 10].",
                "rejected": "Puede reprobar tantas materias como desee."
            },
            {
                "prompt": "<question>¿Dónde presento la tesis?</question>",
                "chosen": "Debe presentarla en la Coordinación de Posgrado [Reglamento, Art. 25].",
                "rejected": "Debe enviarla a cualquier ventanilla."
            },
            {
                "prompt": "<question>¿Cuál es la nota mínima de aprobación?</question>",
                "chosen": "La nota mínima es de 65 puntos [Reglamento, Art. 40].",
                "rejected": "La nota mínima es 51 puntos."
            },
            {
                "prompt": "<question>¿Cuánto dura la prórroga de graduación?</question>",
                "chosen": "La prórroga máxima es de 6 meses previa solicitud [Reglamento, Art. 55].",
                "rejected": "No existen prórrogas bajo ninguna circunstancia."
            },
            {
                "prompt": "<question>¿Qué costo tiene el certificado?</question>",
                "chosen": "No dispongo de esa información en los reglamentos vigentes. [Reglamento, Art. 1]",
                "rejected": "El certificado es gratuito para todos."
            }
        ]
        with open(self.dataset_file, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex) + "\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cpu_optimizations(self):
        config = TrainConfig(
            dataset_path=self.dataset_file,
            output_dir=self.output_dir,
            cpu_threads=8,
            nice_priority=10
        )
        worker = TrainWorker(config)
        worker.apply_cpu_optimizations()
        self.assertEqual(os.environ.get("OMP_NUM_THREADS"), "8")
        self.assertEqual(os.environ.get("MKL_NUM_THREADS"), "8")

    def test_load_dataset_valid_and_invalid(self):
        config = TrainConfig(dataset_path=self.dataset_file, output_dir=self.output_dir)
        worker = TrainWorker(config)
        data = worker.load_dataset(self.dataset_file)
        self.assertEqual(len(data), 5)

        # Dataset no existente
        with self.assertRaises(FileNotFoundError):
            worker.load_dataset(os.path.join(self.test_dir, "non_existent.jsonl"))

        # Dataset vacío
        empty_file = os.path.join(self.test_dir, "empty.jsonl")
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("\n\n")
        with self.assertRaises(ValueError):
            worker.load_dataset(empty_file)

    def test_micro_batch_training_loss_decrease_and_artifacts(self):
        """
        Gate de Control de la Fase 2:
        - Micro-lote sintético de 5 ejemplos.
        - Pérdida final menor que la inicial (convergencia estricta).
        - Generación de artefactos LoRA y Modelfile.
        """
        config = TrainConfig(
            dataset_path=self.dataset_file,
            output_dir=self.output_dir,
            lora_r=8,
            lora_alpha=16,
            num_train_epochs=1,
            cpu_threads=4,
            emulation_mode=True
        )
        worker = TrainWorker(config)
        result = worker.run_training()

        self.assertIn(result.status, ["success", "emulated"])
        self.assertEqual(result.samples_trained, 5)
        self.assertGreater(result.initial_loss, result.final_loss)
        self.assertLess(result.elapsed_time_seconds, 180.0)  # Menos de 3 minutos

        # Verificar existencia y formato de artefactos generados
        adapter_cfg_file = os.path.join(self.output_dir, "adapter_config.json")
        metrics_file = os.path.join(self.output_dir, "training_metrics.json")
        modelfile_path = os.path.join(self.output_dir, "Modelfile")

        self.assertTrue(os.path.exists(adapter_cfg_file))
        self.assertTrue(os.path.exists(metrics_file))
        self.assertTrue(os.path.exists(modelfile_path))

        with open(adapter_cfg_file, "r", encoding="utf-8") as f:
            cfg_data = json.load(f)
            self.assertEqual(cfg_data["r"], 8)
            self.assertEqual(cfg_data["lora_alpha"], 16)
            self.assertEqual(cfg_data["peft_type"], "LORA")
            self.assertEqual(cfg_data["target_modules"], ["q_proj", "v_proj"])

        with open(modelfile_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("FROM llama3.2:latest", content)
            self.assertIn("ADAPTER", content)
            self.assertIn("CLODA-RAG", content)

    def test_async_training_execution(self):
        """Verifica que el reentrenamiento desacoplado en segundo plano reporte progreso."""
        config = TrainConfig(
            dataset_path=self.dataset_file,
            output_dir=self.output_dir,
            emulation_mode=True
        )
        worker = TrainWorker(config)

        progress_recorded = []
        def on_progress(step, total, loss):
            progress_recorded.append((step, total, loss))

        worker.set_progress_callback(on_progress)

        finished_flag = [False]
        def on_finish(result: TrainingResult):
            finished_flag[0] = True

        thread = worker.start_async(on_finish=on_finish)
        self.assertTrue(thread.is_alive())

        # Esperar finalización
        thread.join(timeout=10.0)
        self.assertTrue(finished_flag[0])
        self.assertFalse(worker.is_running)
        self.assertGreater(len(progress_recorded), 0)

        # Probar getter de progreso
        prog = worker.get_progress()
        self.assertEqual(prog["progress_percent"], 100.0)
        self.assertIsNotNone(prog["last_result"])


if __name__ == "__main__":
    unittest.main()
