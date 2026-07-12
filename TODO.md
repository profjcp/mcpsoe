# Fase 2 / Sprint 2 - GraphRAG + Validación + Diagnóstico (Doctorado)

## Objetivo general
Implementar una capa de recuperación relacional (GraphRAG), validación de fuentes y diagnóstico operativo para mejorar veracidad, trazabilidad y desempeño en consultas complejas multi-documento.

---

## Plan de ejecución por pasos (orden recomendado)

### Paso 1 — MVP GraphRAG (prioridad alta)
- [ ] Crear `agents/graph_rag_agent.py`
  - [ ] Construcción de grafo ligero (nodos = chunks, aristas = similitud/co-ocurrencia/categoría)
  - [ ] Método `retrieve_with_graph(question)` con expansión de vecinos
  - [ ] Salida con `context`, `sources`, `graph_trace`, `timing_ms`
- [ ] Actualizar `preprocess.py`
  - [ ] Generar y persistir estructura de grafo (`graph_index.pkl` o `graph_edges.json`)
- [ ] Integrar carga del índice de grafo en `mcp_server_local.py`
- [ ] Integrar fallback condicional `RAG_DOC -> GRAPH_RAG` en `orchestrator/router.py`

### Paso 2 — Validación de fuentes (prioridad alta)
- [ ] Crear `agents/source_validator.py`
  - [ ] `validate_answer_support(answer, sources, context)` -> `support_score`, `unsupported_claims`
- [ ] Integrar validación post-generación en `mcp_server_local.py`
  - [ ] Si soporte bajo: respuesta segura con advertencia y reducción de afirmaciones
- [ ] Persistir nuevos campos en `interaction_logs.jsonl`:
  - [ ] `support_score`
  - [ ] `unsupported_claims_count`
  - [ ] `validation_mode`

### Paso 3 — Métricas y observabilidad (prioridad media)
- [ ] Extender endpoint `/metrics` en `mcp_server_local.py`
  - [ ] `% respuestas con soporte alto`
  - [ ] promedio `support_score`
  - [ ] distribución por `answer_mode` incluyendo `GRAPH_RAG`
- [ ] Incluir trazabilidad en logs para auditoría doctoral

### Sprint 2 — Bloque activo aprobado (orden: 1,2,3)
- [ ] (1) Evaluación automática RAGAS (`evaluation/*`)
  - [x] Refactor `evaluation/ragas_worker.py` para consumir `/ask` streaming y reconstruir respuesta
  - [x] Inferir `actual_type/source` desde `interaction_logs.jsonl`
  - [x] Robustecer cálculo de métricas
  - [x] Mejorar `evaluation/eval_ragas_batch.py` (imports, accuracy por tipo, salida enriquecida)
  - [ ] Actualizar `evaluation/README.md`
- [ ] (2) Fortalecer enrutamiento/observabilidad GRAPH_RAG (backend)
  - [x] `orchestrator/router.py`: ampliar `routing_trace` (motivo, flags, fallback)
  - [x] `mcp_server_local.py`: consistencia de `source` y resumen por `source` en `/metrics`
  - [ ] Verificar no ruptura de streaming
- [ ] (3) Integración cliente/admin
  - [x] `appclient/app_admin.py`: panel de routing (conteo por source, %GRAPH_RAG, tabla de trazas)
  - [x] `appclient/app_client.py`: metadato no invasivo de fuente en última respuesta

### Paso 4 — Dashboard diagnóstico multiagente (prioridad media)
- [ ] Editar `appclient/app_admin.py`
  - [ ] Nueva sección/tab “Diagnóstico Multiagente”
  - [ ] Gráficas por modo: GUIDANCE/FAQ/CACHE/RAG_DOC/GRAPH_RAG
  - [ ] Latencia por modo
  - [ ] Calidad de soporte de fuentes (`support_score`)
  - [ ] Errores por categoría

### Paso 5 — Evaluación experimental Sprint 2 (prioridad alta)
- [ ] Crear `evaluation/datasets/upg_eval_v2.jsonl` (casos multi-hop)
- [ ] Extender `evaluation/eval_ragas_batch.py` para incluir:
  - [ ] faithfulness
  - [ ] context precision
  - [ ] support score
- [ ] Generar reporte comparativo T1 vs T2:
  - [ ] `experiments/RESULTADOS_T2.md`

---

## Criterios de aceptación Sprint 2
- [ ] Existe ruta funcional `GRAPH_RAG` para casos complejos
- [ ] Cada respuesta RAG/GraphRAG tiene validación de soporte
- [ ] Dashboard muestra diagnóstico por modo y soporte de fuentes
- [ ] Evaluación T2 ejecutable y documentada

---

## Riesgos y mitigación
- [ ] Riesgo: latencia extra por expansión de grafo  
      Mitigación: límite de vecinos + cache de subgrafos
- [ ] Riesgo: falsos negativos en validación de soporte  
      Mitigación: umbrales calibrables por categoría
- [ ] Riesgo: complejidad de integración en servidor principal  
      Mitigación: feature flags (`ENABLE_GRAPH_RAG`, `ENABLE_SOURCE_VALIDATION`)

---

## Notas operativas
- Mantener compatibilidad con flujo actual (no romper GUIDANCE/FAQ/CACHE/RAG_DOC).
- Aplicar cambios incrementales por PR pequeño.
- Validar cada paso con pruebas críticas antes de avanzar al siguiente.
