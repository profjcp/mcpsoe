import unittest
import os
import sys

# Asegurar importación de módulos raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import tempfile
import shutil

from continual_learning.model_registry import ModelRegistry, ModelVersion
from continual_learning.train_worker import TrainConfig, TrainWorker


class TestModelRegistry(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.registry_file = os.path.join(self.test_dir, "test_registry.json")
        self.adapter_dir = os.path.join(self.test_dir, "adapter_checkpoint_v1")
        os.makedirs(self.adapter_dir, exist_ok=True)

        # Crear archivo dummy de configuración PEFT
        with open(os.path.join(self.adapter_dir, "adapter_config.json"), "w", encoding="utf-8") as f:
            json.dump({"r": 8, "lora_alpha": 16, "peft_type": "LORA"}, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_default_v0(self):
        registry = ModelRegistry(registry_file=self.registry_file, base_model_default="llama3.2:latest")
        self.assertEqual(registry.active_version_id, "v0")
        self.assertEqual(registry.get_active_model_name(), "llama3.2:latest")
        self.assertIn("v0", registry.versions)
        self.assertTrue(registry.versions["v0"].is_active)
        self.assertTrue(os.path.exists(self.registry_file))

    def test_modelfile_generation(self):
        registry = ModelRegistry(registry_file=self.registry_file)
        modelfile = registry.generate_modelfile(
            adapter_dir=self.adapter_dir,
            base_model="llama3.2:latest",
            temperature=0.2
        )
        self.assertTrue(os.path.exists(modelfile))
        with open(modelfile, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("FROM llama3.2:latest", content)
            self.assertIn(f"ADAPTER {os.path.abspath(self.adapter_dir)}", content)
            self.assertIn("PARAMETER temperature 0.2", content)
            self.assertIn("CLODA-RAG", content)

    def test_version_progression_and_persistence(self):
        registry = ModelRegistry(registry_file=self.registry_file)
        self.assertEqual(registry.get_next_version_id(), "v1")

        # Registrar v1
        v1 = registry.register_version(
            adapter_dir=self.adapter_dir,
            metadata={"loss": 1.25},
            mock_mode=True
        )
        self.assertEqual(v1.version_id, "v1")
        self.assertEqual(v1.model_name, "soebot:v1")
        self.assertEqual(registry.get_next_version_id(), "v2")

        # Registrar v2
        adapter_v2 = os.path.join(self.test_dir, "adapter_v2")
        os.makedirs(adapter_v2, exist_ok=True)
        v2 = registry.register_version(adapter_v2, mock_mode=True)
        self.assertEqual(v2.version_id, "v2")
        self.assertEqual(v2.model_name, "soebot:v2")

        # Verificar recarga desde archivo persistido
        registry_reloaded = ModelRegistry(registry_file=self.registry_file)
        self.assertEqual(len(registry_reloaded.versions), 3)  # v0, v1, v2
        self.assertIn("v1", registry_reloaded.versions)
        self.assertIn("v2", registry_reloaded.versions)

    def test_activation_and_hot_reload_callback(self):
        registry = ModelRegistry(registry_file=self.registry_file)
        v1 = registry.register_version(self.adapter_dir, mock_mode=True)

        reloaded_models = []
        def mock_reload_fn(model_name: str) -> bool:
            reloaded_models.append(model_name)
            return True

        # Activar v1
        ok = registry.activate_version("v1", reload_callback=mock_reload_fn)
        self.assertTrue(ok)
        self.assertEqual(registry.active_version_id, "v1")
        self.assertEqual(registry.get_active_model_name(), "soebot:v1")
        self.assertTrue(registry.versions["v1"].is_active)
        self.assertFalse(registry.versions["v0"].is_active)
        self.assertEqual(reloaded_models, ["soebot:v1"])

        # Intentar activar versión inexistente
        bad_ok = registry.activate_version("v99")
        self.assertFalse(bad_ok)

    def test_end_to_end_closed_loop_train_and_register(self):
        """
        Gate de Control de Fase 4:
        Valida el flujo continuo completo:
        1. TrainWorker genera adaptador LoRA y artefactos.
        2. ModelRegistry compila y registra el nuevo modelo soebot:v1.
        3. Se activa en caliente mediante el reload_callback.
        """
        # 1. Crear dataset sintético
        dataset_path = os.path.join(self.test_dir, "train.jsonl")
        with open(dataset_path, "w", encoding="utf-8") as f:
            for i in range(5):
                f.write(json.dumps({
                    "prompt": f"¿Regla {i}?",
                    "chosen": f"Respuesta fáctica {i} [Reglamento, Art. {i}]",
                    "rejected": f"Alucinación {i}"
                }) + "\n")

        out_adapter = os.path.join(self.test_dir, "adapters", "v1_ckpt")
        train_worker = TrainWorker(TrainConfig(
            dataset_path=dataset_path,
            output_dir=out_adapter,
            emulation_mode=True
        ))
        train_result = train_worker.run_training()
        self.assertEqual(train_result.status, "emulated")
        self.assertTrue(os.path.exists(os.path.join(out_adapter, "adapter_config.json")))

        # 2. Registrar en ModelRegistry
        registry = ModelRegistry(registry_file=self.registry_file)
        new_ver = registry.register_version(
            adapter_dir=train_result.output_dir,
            metadata=train_result.metadata,
            mock_mode=True
        )
        self.assertEqual(new_ver.version_id, "v1")
        self.assertEqual(new_ver.model_name, "soebot:v1")

        # 3. Recarga en caliente simulada
        runtime_llm = {"active": "llama3.2:latest"}
        def hot_reload_runtime(model_name: str) -> bool:
            runtime_llm["active"] = model_name
            return True

        success = registry.activate_version("v1", reload_callback=hot_reload_runtime)
        self.assertTrue(success)
        self.assertEqual(runtime_llm["active"], "soebot:v1")
        self.assertEqual(registry.get_active_model_name(), "soebot:v1")


if __name__ == "__main__":
    unittest.main()
