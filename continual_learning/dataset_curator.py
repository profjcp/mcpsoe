#!/usr/bin/env python3
"""
Sintetizador y Curador Autónomo de Datasets de Preferencia (DPO / SFT)
=====================================================================
Componente Central de la Fase 1 de CLODA-RAG (Tesis Doctoral).

Transforma autónomamente los fallos detectados por el Verificador Fáctico NLI,
las discrepancias de simulación y el feedback de usuario en pares de entrenamiento
para alineación continua (Direct Preference Optimization & Supervised Fine-Tuning).
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
import os
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@dataclass
class DPOTriplet:
    """Terna de optimización de preferencias directas (DPO)."""
    id: str
    prompt: str
    chosen: str
    rejected: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SFTExample:
    """Ejemplo para ajuste supervisado (SFT)."""
    instruction: str
    input: str
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetCurator:
    """
    Minero y Curador de Datasets a partir de telemetría y resultados de auditoría.
    """

    SYSTEM_INSTRUCTION = (
        "Eres SoeBOT, asistente de posgrado oficial de la UAGRM. "
        "Responde con exactitud basándote estrictamente en el reglamento proporcionado. "
        "Si la información no está en el texto, emite la frase de contingencia sin inventar. "
        "Incluye siempre la cita formal [Doc, Art]."
    )

    CONTINGENCY_ANSWER = (
        "No dispongo de esa información en los reglamentos vigentes. "
        "Por favor, acude a la Jefatura Académica."
    )

    def __init__(self, min_text_len: int = 15):
        self.min_text_len = min_text_len
        self.dpo_pairs: List[DPOTriplet] = []
        self.sft_examples: List[SFTExample] = []
        self._seen_prompts: set = set()

    def clean_text(self, text: str) -> str:
        """Limpia saltos de línea repetidos y espacios innecesarios."""
        if not text:
            return ""
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def format_prompt(self, question: str, context: str = "") -> str:
        """Formatea el prompt unificado en estilo XML / Instructivo para el SLM."""
        q_clean = self.clean_text(question)
        c_clean = self.clean_text(context)
        if c_clean:
            return f"<context>\n{c_clean}\n</context>\n\n<question>\n{q_clean}\n</question>"
        return f"<question>\n{q_clean}\n</question>"

    def mine_from_simulation_results(self, json_filepath: str) -> int:
        """
        Mina pares DPO y SFT desde archivos consolidados de simulación
        (ej. simulation_results/resultados_100.json).
        """
        if not os.path.exists(json_filepath):
            logging.warning(f"DatasetCurator: Archivo no encontrado: {json_filepath}")
            return 0

        with open(json_filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                logging.error(f"DatasetCurator: Error leyendo JSON {json_filepath}: {e}")
                return 0

        items = data.get("resultados", [])
        extracted_dpo = 0

        for idx, item in enumerate(items):
            question = item.get("question", "").strip()
            response = item.get("response", "").strip()
            expected = item.get("expected_answer", "").strip()
            clasificacion = item.get("clasificacion", "")
            in_context = item.get("in_context", True)

            if not question or len(response) < self.min_text_len:
                continue

            prompt = self.format_prompt(question)

            # Caso 1: Posible Alucinación -> Candidato prioritario para DPO
            if clasificacion == "posible_alucinacion" and expected:
                if prompt in self._seen_prompts:
                    continue

                # Formatear la respuesta elegida con cita formal si falta
                chosen_text = expected
                if not ("[" in chosen_text and "]" in chosen_text):
                    chosen_text = f"{expected} [Reglamento General, Art. 1]"

                dpo_item = DPOTriplet(
                    id=f"sim_dpo_{idx:04d}",
                    prompt=prompt,
                    chosen=self.clean_text(chosen_text),
                    rejected=self.clean_text(response),
                    metadata={
                        "source_file": os.path.basename(json_filepath),
                        "user_role": item.get("user_role", ""),
                        "area": item.get("area", ""),
                        "clasificacion": clasificacion,
                    }
                )
                self.dpo_pairs.append(dpo_item)
                self._seen_prompts.add(prompt)
                extracted_dpo += 1

            # Caso 2: Respuesta Correcta con Contexto -> Útil para SFT
            elif clasificacion == "correcta" and response:
                sft_item = SFTExample(
                    instruction=self.SYSTEM_INSTRUCTION,
                    input=prompt,
                    output=self.clean_text(response),
                    metadata={
                        "source_file": os.path.basename(json_filepath),
                        "user_role": item.get("user_role", ""),
                        "area": item.get("area", ""),
                    }
                )
                self.sft_examples.append(sft_item)

        logging.info(
            f"DatasetCurator: Minados {extracted_dpo} pares DPO y {len(self.sft_examples)} "
            f"ejemplos SFT desde {json_filepath}"
        )
        return extracted_dpo

    def mine_from_interaction_logs(self, jsonl_filepath: str) -> int:
        """
        Mina pares DPO desde interaction_logs.jsonl a partir de veredictos NLI
        donde is_hallucinated=True o p_contradiction > 0.45.
        """
        if not os.path.exists(jsonl_filepath):
            logging.info(f"DatasetCurator: interaction_logs.jsonl aún no existe en: {jsonl_filepath}")
            return 0

        extracted_dpo = 0
        with open(jsonl_filepath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                question = record.get("question", "").strip()
                response_text = record.get("response_text", "").strip()
                hallucinated = bool(record.get("hallucinated", False))
                routing_trace = record.get("routing_trace", {}) or {}
                nli_audit = routing_trace.get("nli_audit", {}) or {}
                sources = record.get("sources", []) or []

                p_contra = float(nli_audit.get("p_contradiction", 0.0))
                is_nli_hallucinated = bool(nli_audit.get("is_hallucinated", False))

                # Extraer contexto documental si existe
                context_parts = []
                for s in sources:
                    snippet = s.get("snippet", "") or s.get("text", "")
                    title = s.get("title", "")
                    sec = s.get("section", "")
                    if snippet:
                        citation = f"[{title}, {sec}]" if (title or sec) else ""
                        context_parts.append(f"{citation} {snippet}".strip())
                context_str = "\n\n".join(context_parts)

                prompt = self.format_prompt(question, context_str)

                # Si hubo alucinación confirmada por NLI o por grader
                if (hallucinated or is_nli_hallucinated or p_contra > 0.45) and len(response_text) >= self.min_text_len:
                    if prompt in self._seen_prompts:
                        continue

                    # La respuesta correcta es la contingencia formal o el fragmento fáctico
                    chosen = self.CONTINGENCY_ANSWER
                    if context_parts:
                        chosen = f"Según la normativa oficial: {context_parts[0]}"
                        if not ("[" in chosen and "]" in chosen):
                            chosen += " [Reglamento UAGRM]"

                    dpo_item = DPOTriplet(
                        id=f"log_dpo_{idx:05d}",
                        prompt=prompt,
                        chosen=chosen,
                        rejected=self.clean_text(response_text),
                        metadata={
                            "timestamp": record.get("timestamp", ""),
                            "user_id": record.get("user_id", ""),
                            "p_contradiction": p_contra,
                            "source_agent": record.get("source", ""),
                        }
                    )
                    self.dpo_pairs.append(dpo_item)
                    self._seen_prompts.add(prompt)
                    extracted_dpo += 1

        logging.info(f"DatasetCurator: Minados {extracted_dpo} pares DPO desde {jsonl_filepath}")
        return extracted_dpo

    def export_datasets(self, output_dir: str) -> Tuple[str, str]:
        """Guarda los datasets minados en disco en formato JSONL."""
        os.makedirs(output_dir, exist_ok=True)
        dpo_path = os.path.join(output_dir, "dpo_train.jsonl")
        sft_path = os.path.join(output_dir, "sft_train.jsonl")

        with open(dpo_path, "w", encoding="utf-8") as f:
            for item in self.dpo_pairs:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

        with open(sft_path, "w", encoding="utf-8") as f:
            for item in self.sft_examples:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

        logging.info(f"DatasetCurator: Exportado DPO ({len(self.dpo_pairs)} filas) -> {dpo_path}")
        logging.info(f"DatasetCurator: Exportado SFT ({len(self.sft_examples)} filas) -> {sft_path}")
        return dpo_path, sft_path

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumen estadístico de curación."""
        return {
            "total_dpo_pairs": len(self.dpo_pairs),
            "total_sft_examples": len(self.sft_examples),
            "unique_prompts": len(self._seen_prompts),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Curador Autónomo de Datasets CLODA-RAG")
    parser.add_argument("--sim-file", default="simulation_results/resultados_100.json", help="Ruta de resultados de simulación")
    parser.add_argument("--log-file", default="interaction_logs.jsonl", help="Ruta de logs de interacción")
    parser.add_argument("--output-dir", default="continual_learning/datasets", help="Directorio de salida")
    args = parser.parse_args()

    curator = DatasetCurator()
    curator.mine_from_simulation_results(args.sim_file)
    curator.mine_from_interaction_logs(args.log_file)
    curator.export_datasets(args.output_dir)
    print("Resumen de Curación:", curator.get_summary())
