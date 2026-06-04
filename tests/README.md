# Suite de Pruebas - SoeBOT (Sprint 1 Multi-Agente)

Esta carpeta concentra la estrategia y ejecución de pruebas para:
- Backend API (FastAPI)
- Smoke tests de cliente/UI
- Verificación de trazabilidad (`sources`, `routing_trace`)
- Evidencias de resultados para documentación/tesis

## 1) Objetivo

Validar que la integración multi-agente (GUIDANCE/FAQ/CACHE/RAG_DOC) funcione sin romper:
- Flujo de respuestas del chatbot
- Endpoints existentes (`/ask`, `/feedback`, `/metrics`, `/health`)
- Persistencia de logs y métricas

## 2) Cobertura

### Backend/API (thorough)
- `GET /health`
- `POST /ask`
  - Happy path: GUIDANCE
  - Happy path: FAQ
  - Happy path: CACHE (repetición misma pregunta)
  - Happy path: RAG_DOC (consulta no FAQ pero del dominio)
  - Error path: payload inválido (422)
  - Error path: JSON inválido (422)
- `POST /feedback`
  - Happy path
  - Error path (campos faltantes / tipos incorrectos)
- `GET /metrics`
  - Estructura consistente
  - Campos cuantitativos/cualitativos presentes

### Smoke UI
- Carga del cliente
- Envío de pregunta y render de respuesta
- Flujo básico de feedback

### Persistencia y trazabilidad
- Verificar en `interaction_logs.jsonl`:
  - `source`
  - `sources`
  - `routing_trace`
  - `confidence`
  - `timing_ms`

## 3) Precondiciones

1. Ollama y Redis activos.
2. Índices FAISS disponibles (`faiss_index.bin`, `chunks.pkl`).
3. Servidor levantado en `http://localhost:9000`.
4. Cliente opcional en `http://localhost:8501`.

## 4) Ejecución rápida

```bash
bash tests/smoke/run_smoke_api.sh
```

## 5) Ejecución manual (curl)

### Health
```bash
curl -s http://localhost:9000/health
```

### Ask - GUIDANCE
```bash
curl -s -X POST http://localhost:9000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"hola","user_id":"qa_guidance"}'
```

### Ask - FAQ
```bash
curl -s -X POST http://localhost:9000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cuáles son los documentos de inscripción?","user_id":"qa_faq"}'
```

### Ask - CACHE (repetir la misma pregunta)
```bash
curl -s -X POST http://localhost:9000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cuáles son los documentos de inscripción?","user_id":"qa_faq"}'
```

### Ask - RAG_DOC (ejemplo)
```bash
curl -s -X POST http://localhost:9000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Explica la diferencia entre plan de estudios y malla curricular","user_id":"qa_rag"}'
```

### Ask - inválido (422)
```bash
curl -s -X POST http://localhost:9000/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"qa_invalid"}'
```

### Feedback - happy path
```bash
curl -s -X POST http://localhost:9000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "question":"¿Cuáles son los documentos de inscripción?",
    "response":"...",
    "user_id":"qa_feedback",
    "satisfaction":5,
    "clarity":5,
    "completeness":4,
    "error_type":"",
    "comments":"ok"
  }'
```

### Feedback - error (422)
```bash
curl -s -X POST http://localhost:9000/feedback \
  -H "Content-Type: application/json" \
  -d '{"question":"x","response":"y","user_id":"qa_feedback"}'
```

### Metrics
```bash
curl -s http://localhost:9000/metrics
```

## 6) Evidencias

Guardar resultados en:
- `tests/results/smoke_api_latest.md` (resumen legible)
- `tests/results/curl_raw/` (salidas crudas opcionales)

## 7) Criterios de aceptación Sprint 1

- [ ] `/health` responde `healthy`
- [ ] `/ask` cubre GUIDANCE/FAQ/CACHE/RAG_DOC
- [ ] `/ask` inválido devuelve 422
- [ ] `/feedback` happy/error verificados
- [ ] `/metrics` consistente
- [ ] `interaction_logs.jsonl` contiene `sources/routing_trace/confidence/timing_ms`
- [ ] Smoke UI básico sin ruptura de streaming
