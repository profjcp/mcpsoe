import argparse
import csv
import json
import os
import random
import re
import string
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from statistics import mean, median

import requests


FAQ_FILES = {
    "AtencionCliente": "documentos/faq_atencion_cliente.txt",
    "Academica": "documentos/faq_academica.txt",
    "Investigacion": "documentos/faq_investigacion.txt",
}


@dataclass
class TestCase:
    domain: str
    original_question: str
    expected_answer: str
    variant_question: str
    variant_type: str


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str):
    return re.findall(r"[a-z0-9_]+", normalize_text(text))


def similarity_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def jaccard_overlap(a: str, b: str) -> float:
    ta = set(tokenize(a))
    tb = set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta.intersection(tb)) / len(ta.union(tb))


def maybe_typo(text: str, rng: random.Random) -> str:
    words = text.split()
    if not words:
        return text
    idx = rng.randrange(len(words))
    word = words[idx]
    if len(word) > 4:
        remove_at = rng.randrange(1, len(word) - 1)
        word = word[:remove_at] + word[remove_at + 1 :]
    words[idx] = word
    return " ".join(words)


def paraphrase_light(question: str, rng: random.Random) -> str:
    replacements = {
        "como": ["de que forma", "cual es la forma", "de que manera"],
        "cuales": ["que", "podrias indicar cuales"],
        "puedo": ["se puede", "es posible"],
        "requisitos": ["condiciones", "requerimientos"],
        "documentos": ["papeles", "documentacion"],
        "horarios": ["horas de atencion", "franja horaria"],
    }
    q_norm = normalize_text(question)
    out = q_norm
    for key, vals in replacements.items():
        if key in out and rng.random() < 0.45:
            out = out.replace(key, rng.choice(vals), 1)
    return out.capitalize() + "?"


def make_variants(question: str, rng: random.Random):
    base = question.strip()
    no_accents = normalize_text(base)
    typo = maybe_typo(base, rng)
    para = paraphrase_light(base, rng)
    return [
        (base, "original"),
        (no_accents, "sin_acentos"),
        (typo, "typo_leve"),
        (para, "parafrasis"),
    ]


def parse_faq_file(path: str):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    rows = []
    current_q = None
    current_a_lines = []

    def flush():
        nonlocal current_q, current_a_lines
        if current_q and current_a_lines:
            answer = "\n".join(current_a_lines).strip()
            if answer:
                rows.append((current_q.strip(), answer))
        current_q = None
        current_a_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Pregunta:"):
            flush()
            current_q = stripped.replace("Pregunta:", "", 1).strip()
            continue

        if stripped.startswith("Respuesta:"):
            payload = stripped.replace("Respuesta:", "", 1).strip()
            if payload:
                current_a_lines.append(payload)
            continue

        if current_q is not None:
            if stripped == "":
                current_a_lines.append("")
            else:
                current_a_lines.append(line)

    flush()
    return rows


def extract_answer_section(full_text: str) -> str:
    text = full_text.strip()
    if "Respuesta:" in text:
        return text.split("Respuesta:")[-1].strip()
    return text


def call_ask(base_url: str, question: str, user_id: str, timeout: int):
    url = f"{base_url.rstrip('/')}/ask"
    started = time.perf_counter()
    response_text = ""

    try:
        with requests.post(
            url,
            json={"question": question, "user_id": user_id},
            stream=True,
            timeout=timeout,
        ) as resp:
            status_code = resp.status_code
            if status_code >= 400:
                elapsed_ms = (time.perf_counter() - started) * 1000
                return {
                    "ok": False,
                    "status_code": status_code,
                    "latency_ms": round(elapsed_ms, 2),
                    "response_text": "",
                    "error": f"HTTP {status_code}",
                }

            for chunk in resp.iter_content(chunk_size=None):
                if chunk:
                    response_text += chunk.decode("utf-8", errors="ignore")

            elapsed_ms = (time.perf_counter() - started) * 1000
            return {
                "ok": True,
                "status_code": status_code,
                "latency_ms": round(elapsed_ms, 2),
                "response_text": response_text,
                "error": "",
            }

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "ok": False,
            "status_code": 0,
            "latency_ms": round(elapsed_ms, 2),
            "response_text": "",
            "error": str(exc),
        }


def percentile(values, p):
    if not values:
        return 0.0
    data = sorted(values)
    if len(data) == 1:
        return float(data[0])
    idx = (len(data) - 1) * (p / 100.0)
    lo = int(idx)
    hi = min(lo + 1, len(data) - 1)
    frac = idx - lo
    return data[lo] * (1 - frac) + data[hi] * frac


def build_cases(rng: random.Random, max_cases_per_domain: int):
    cases = []
    for domain, file_path in FAQ_FILES.items():
        items = parse_faq_file(file_path)
        if not items:
            continue

        sampled = items if max_cases_per_domain <= 0 else items[:max_cases_per_domain]
        for q, a in sampled:
            for vq, vtype in make_variants(q, rng):
                cases.append(TestCase(domain, q, a, vq, vtype))

    if not cases:
        raise RuntimeError("No se pudieron construir casos desde archivos FAQ.")
    return cases


def auto_feedback_score(passed: bool, latency_ms: float):
    if passed and latency_ms < 1500:
        return 5, 5, 5
    if passed and latency_ms < 4000:
        return 4, 4, 4
    if passed:
        return 3, 3, 3
    return 2, 2, 2


def post_feedback(base_url: str, question: str, response: str, passed: bool, latency_ms: float, timeout: int):
    sat, clar, comp = auto_feedback_score(passed, latency_ms)
    payload = {
        "question": question,
        "response": response,
        "satisfaction": sat,
        "clarity": clar,
        "completeness": comp,
        "error_type": "" if passed else "Evaluacion automatica: respuesta no alineada",
        "comments": "Feedback automatico generado por bateria T1",
    }
    try:
        requests.post(f"{base_url.rstrip('/')}/feedback", json=payload, timeout=timeout)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Batería automática T1 para SoeBOT")
    parser.add_argument("--base-url", default="http://127.0.0.1:9000", help="URL base del backend")
    parser.add_argument("--requests", type=int, default=300, help="Número total de consultas")
    parser.add_argument("--users", type=int, default=12, help="Número de usuarios simulados")
    parser.add_argument("--concurrency", type=int, default=8, help="Hilos concurrentes")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad")
    parser.add_argument("--timeout", type=int, default=90, help="Timeout por request en segundos")
    parser.add_argument("--similarity-threshold", type=float, default=0.45, help="Umbral de similitud automática")
    parser.add_argument("--overlap-threshold", type=float, default=0.20, help="Umbral de overlap tokens")
    parser.add_argument("--max-cases-per-domain", type=int, default=0, help="0 = usar todos")
    parser.add_argument("--warmup", type=int, default=5, help="Consultas de calentamiento")
    parser.add_argument("--send-auto-feedback", action="store_true", help="Enviar feedback automático")
    parser.add_argument("--out-dir", default="experiments/results", help="Carpeta raíz de resultados")

    args = parser.parse_args()
    rng = random.Random(args.seed)

    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.out_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    cases = build_cases(rng, args.max_cases_per_domain)

    users = [f"sim_user_{i:03d}" for i in range(1, args.users + 1)]
    user_profiles = {}
    profile_types = ["externo", "administrativo", "academico"]
    for user in users:
        user_profiles[user] = rng.choice(profile_types)

    # Warmup
    for _ in range(max(0, args.warmup)):
        tc = rng.choice(cases)
        _ = call_ask(args.base_url, tc.variant_question, rng.choice(users), args.timeout)

    schedule = []
    for i in range(args.requests):
        tc = rng.choice(cases)
        user = users[i % len(users)]
        schedule.append((i + 1, user, user_profiles[user], tc))

    rows = []

    def worker(job):
        idx, user_id, user_type, tc = job
        result = call_ask(args.base_url, tc.variant_question, user_id, args.timeout)

        response_full = result["response_text"]
        response_main = extract_answer_section(response_full)
        sim = similarity_ratio(response_main, tc.expected_answer)
        overlap = jaccard_overlap(response_main, tc.expected_answer)
        faq_pattern = "Respuesta (" in response_full or "Pregunta:" in response_full

        passed = (sim >= args.similarity_threshold) or (overlap >= args.overlap_threshold)
        if not result["ok"]:
            passed = False

        if args.send_auto_feedback and result["ok"]:
            post_feedback(args.base_url, tc.variant_question, response_full, passed, result["latency_ms"], args.timeout)

        return {
            "run_id": run_id,
            "request_id": idx,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "user_type": user_type,
            "domain_expected": tc.domain,
            "question_original": tc.original_question,
            "question_variant": tc.variant_question,
            "variant_type": tc.variant_type,
            "expected_answer": tc.expected_answer,
            "response": response_full,
            "response_main": response_main,
            "http_status": result["status_code"],
            "success": result["ok"],
            "latency_ms": result["latency_ms"],
            "similarity": round(sim, 4),
            "overlap": round(overlap, 4),
            "faq_pattern_detected": faq_pattern,
            "passed_auto_eval": passed,
            "error": result["error"],
        }

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = [executor.submit(worker, job) for job in schedule]
        for fut in as_completed(futures):
            rows.append(fut.result())

    rows.sort(key=lambda x: x["request_id"])

    csv_path = os.path.join(run_dir, "detailed_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    latencies = [r["latency_ms"] for r in rows]
    total = len(rows)
    ok_count = sum(1 for r in rows if r["success"])
    pass_count = sum(1 for r in rows if r["passed_auto_eval"])
    faq_hits = sum(1 for r in rows if r["faq_pattern_detected"])

    by_domain = {}
    for r in rows:
        d = r["domain_expected"]
        by_domain.setdefault(d, {"total": 0, "ok": 0, "passed": 0, "lat": []})
        by_domain[d]["total"] += 1
        by_domain[d]["ok"] += 1 if r["success"] else 0
        by_domain[d]["passed"] += 1 if r["passed_auto_eval"] else 0
        by_domain[d]["lat"].append(r["latency_ms"])

    summary = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "config": {
            "base_url": args.base_url,
            "requests": args.requests,
            "users": args.users,
            "concurrency": args.concurrency,
            "seed": args.seed,
            "timeout": args.timeout,
            "similarity_threshold": args.similarity_threshold,
            "overlap_threshold": args.overlap_threshold,
            "max_cases_per_domain": args.max_cases_per_domain,
            "warmup": args.warmup,
            "send_auto_feedback": args.send_auto_feedback,
        },
        "global_metrics": {
            "total_requests": total,
            "success_count": ok_count,
            "success_rate": round(ok_count / total if total else 0.0, 4),
            "auto_pass_count": pass_count,
            "auto_pass_rate": round(pass_count / total if total else 0.0, 4),
            "faq_pattern_ratio": round(faq_hits / total if total else 0.0, 4),
            "latency_avg_ms": round(mean(latencies), 2) if latencies else 0.0,
            "latency_median_ms": round(median(latencies), 2) if latencies else 0.0,
            "latency_p95_ms": round(percentile(latencies, 95), 2) if latencies else 0.0,
            "latency_p99_ms": round(percentile(latencies, 99), 2) if latencies else 0.0,
        },
        "by_domain": {
            d: {
                "total": vals["total"],
                "success_rate": round(vals["ok"] / vals["total"], 4) if vals["total"] else 0.0,
                "auto_pass_rate": round(vals["passed"] / vals["total"], 4) if vals["total"] else 0.0,
                "latency_avg_ms": round(mean(vals["lat"]), 2) if vals["lat"] else 0.0,
                "latency_p95_ms": round(percentile(vals["lat"], 95), 2) if vals["lat"] else 0.0,
            }
            for d, vals in by_domain.items()
        },
    }

    summary_path = os.path.join(run_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    config_path = os.path.join(run_dir, "config_used.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(summary["config"], f, indent=2, ensure_ascii=False)

    print(f"\n✅ Corrida completada: {run_id}")
    print(f"📁 Resultados: {run_dir}")
    print(f"📄 Detalle: {csv_path}")
    print(f"📄 Resumen: {summary_path}")
    print("\n--- Métricas globales ---")
    for k, v in summary["global_metrics"].items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
