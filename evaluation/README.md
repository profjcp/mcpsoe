# Sistema de Evaluación - SoeBOT

## Propósito

Plantillas para que el investigador doctoral evalúe el sistema multiagente de forma estructurada.

## Estructura

```
evaluation/
├── README.md              # Este archivo
├── datasets/
│   └── upg_eval_v1.jsonl  # Dataset de evaluación inicial
├── ragas_worker.py       # Worker para métricas RAGAs
└── eval_ragas_batch.py  # Evaluación por lotes
```

## Uso

### 1. Preparar dataset de evaluación

Editar `datasets/upg_eval_v1.jsonl` con preguntas de prueba por dominio:

```json
{"question": "¿Cuál es el costo?", "expected_domain": "AtencionCliente", "type": "faq"}
{"question": "¿Cómo defiendo mi tesis?", "expected_domain": "Investigacion", "type": "rag"}
```

### 2. Ejecutar evaluación por lotes

```bash
python evaluation/eval_ragas_batch.py \
  --dataset evaluation/datasets/upg_eval_v1.jsonl \
  --base-url http://127.0.0.1:9000 \
  --output evaluation/results/eval_results_v2_canonical.json
```

### 3. Flujo actual del worker (Sprint 2)

`ragas_worker.py` ahora:
- consume `/ask` en modo streaming (`stream=True`) y reconstruye la respuesta completa.
- consulta `interaction_logs.jsonl` para inferir el `actual_type/source` más reciente por `user_id` y `question`.
- expone campos enriquecidos por caso: `actual_type`, `actual_type_canonical`, `context`, `sources`, `routing_trace`.
- aplica normalización canónica de tipos para evaluación estable:
  - `CACHE -> FAQ`
  - `RAG_DOC/GRAPH_RAG/RAG -> RAG`

### 4. Métricas y salidas

`eval_ragas_batch.py` reporta:
- Faithfulness
- Answer Relevancy
- Context Precision
- Context Recall
- Type Accuracy global
- Type Accuracy por tipo esperado (faq/rag/guidance)

Además guarda salida JSON enriquecida en el archivo indicado por `--output`.

## Notas operativas

- Para resultados consistentes, ejecutar el servidor FastAPI antes de la batería:
  - `python mcp_server_local.py`
- Si hay timeouts en casos largos, repetir corrida o ajustar timeout del entorno de prueba.
- El análisis de tipo usa primero `actual_type_canonical` y, en fallback, `actual_type`.

## Próximos Pasos

- [ ] Agregar más casos de prueba multi-hop (v2)
- [ ] Integrar la corrida en pipeline de experimentos
- [ ] Consolidar reporte comparativo T1 vs T2
