#!/usr/bin/env python3
"""
Evaluación por lotes - SoeBOT
Uso: python evaluation/eval_ragas_batch.py --dataset evaluation/datasets/upg_eval_v1.jsonl
"""
import json
import argparse
import sys
from datetime import datetime
from collections import defaultdict

try:
    from evaluation.ragas_worker import RAGAsWorker
except Exception:
    from ragas_worker import RAGAsWorker


def load_dataset(path: str):
    """Carga dataset de evaluación."""
    cases = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def main():
    parser = argparse.ArgumentParser(description="Evaluación RAGAs por lotes")
    parser.add_argument("--dataset", default="evaluation/datasets/upg_eval_v1.jsonl")
    parser.add_argument("--base-url", default="http://localhost:9000")
    parser.add_argument("--output", default="evaluation/results/eval_results.json")
    args = parser.parse_args()
    
    print(f"📂 Cargando dataset: {args.dataset}")
    cases = load_dataset(args.dataset)
    print(f"📊 Casos a evaluar: {len(cases)}")
    
    worker = RAGAsWorker(base_url=args.base_url)
    results = []
    
    print("\n🔄 Ejecutando evaluación...")
    for i, case in enumerate(cases, 1):
        question = case.get("question", "")
        expected = case.get("expected_type", "unknown")
        
        print(f"  [{i}/{len(cases)}] {question[:50]}...")
        
        result = worker.evaluate_case(question, expected)
        results.append(result)
        
        if result.get("success"):
            print(f"      ✓ faithfulness: {result.get('faithfulness', 0):.2f}")
        else:
            print(f"      ✗ Error: {result.get('error', 'unknown')}")
    
    # Calculate averages and type accuracy
    successful = [r for r in results if r.get("success")]
    if successful:
        avg_faithfulness = sum(r.get("faithfulness", 0) for r in successful) / len(successful)
        avg_relevancy = sum(r.get("answer_relevancy", 0) for r in successful) / len(successful)
        avg_precision = sum(r.get("context_precision", 0) for r in successful) / len(successful)
        avg_recall = sum(r.get("context_recall", 0) for r in successful) / len(successful)
    else:
        avg_faithfulness = avg_relevancy = avg_precision = avg_recall = 0.0

    by_type = defaultdict(lambda: {"total": 0, "ok": 0})
    for r in successful:
        expected_type = str(r.get("expected_type", "UNKNOWN")).upper()
        actual_type = str(r.get("actual_type", "UNKNOWN")).upper()
        actual_type_canonical = str(r.get("actual_type_canonical", actual_type)).upper()
        by_type[expected_type]["total"] += 1
        if expected_type == actual_type_canonical:
            by_type[expected_type]["ok"] += 1

    per_type_accuracy = {
        k: (v["ok"] / v["total"] if v["total"] else 0.0)
        for k, v in by_type.items()
    }
    overall_type_accuracy = (
        sum(v["ok"] for v in by_type.values()) / sum(v["total"] for v in by_type.values())
        if by_type else 0.0
    )

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(cases),
        "successful": len(successful),
        "failed": len(cases) - len(successful),
        "avg_faithfulness": avg_faithfulness,
        "avg_answer_relevancy": avg_relevancy,
        "avg_context_precision": avg_precision,
        "avg_context_recall": avg_recall,
        "overall_type_accuracy": overall_type_accuracy,
        "per_type_accuracy": per_type_accuracy,
        "results": results
    }
    
    # Save results
    import os
    os.makedirs("evaluation/results", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Evaluación completada")
    print(f"   Exitosos: {len(successful)}/{len(cases)}")
    print(f"   Faithfulness: {avg_faithfulness:.2f}")
    print(f"   Answer Relevancy: {avg_relevancy:.2f}")
    print(f"   Context Precision: {avg_precision:.2f}")
    print(f"   Context Recall: {avg_recall:.2f}")
    print(f"   Type Accuracy (global): {overall_type_accuracy:.2f}")
    if per_type_accuracy:
        print("   Type Accuracy (por tipo):")
        for t, acc in per_type_accuracy.items():
            print(f"      - {t}: {acc:.2f}")
    print(f"   Resultados: {args.output}")
    
    return 0 if successful else 1


if __name__ == "__main__":
    sys.exit(main())
