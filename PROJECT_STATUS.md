# Estado del Proyecto SoeBOT

## 📌resumen rápido

**Versión actual**: 2.0 (Pipeline Multiagente)
**Última actualización**: 2026-07-18

---

## ✅ COMPLETADO

### Infraestructura base
- [x] Servidor FastAPI (`mcp_server_local.py`)
- [x] Cliente Streamlit (`appclient/app_client.py`)
- [x] Dashboard Admin (`appclient/app_admin.py`)
- [x] Entorno virtual (`venmcp/`)
- [x] Scripts de ejecución (`run.sh`, `run_clean.sh`)

### Pipeline Multiagente (Sprint 1)
- [x] MultiAgentOrchestrator (`orchestrator/router.py`)
- [x] FAQAgent (`agents/faq_agent.py`)
- [x] DocRAGAgent (`agents/rag_doc_agent.py`)
- [x] Routing GUIDANCE → FAQ → CACHE → RAG_DOC
- [x] Guardrails léxicos para tesis/investigación
- [x] Métricas Prometheus

### Evaluación
- [x] Templates evaluación (`evaluation/`)
- [x] Dataset `upg_eval_v1.jsonl`
- [x] RAGAs worker

### Despliegue
- [x] Service systemd (`deploy/systemd/soebot.service`)
- [x] Scripts install/uninstall

---

## ⏳ PENDIENTE (Priorizado)

### Alta prioridad
1. **GraphRAG** - Relaciones entre documentos
2. **Validación de fuentes** - Verificar citas en respuestas

### Media prioridad
3. **Feedback loop** - Reentrenamiento automático
4. **Dashboard diagnóstico** - Estado de agentes

### Baja prioridad
5. Exportación PDF
6. Base de datos histórica
7. API predictiva

---

## 🚀 Próximo paso recomendado

**GraphRAG** - Para manejar consultas complejas que requieren múltiples documentos

---

## 📊 Métricas actuales (último benchmark)

| Métrica | Valor objetivo | Estado |
|---------|--------------|--------|
| FAQ latency | < 0.5s | ⚡ OK |
| RAG latency | < 3s | ⏳ |
| Cache hit rate | > 60% | ⏳ |
| Hallucination rate | < 3% | ⏳ |
| Success rate | > 97% | ⏳ |

---

## 🐛 Issues conocidos

1. Concurrency > 3 degrada latencia (documentado en T1)
2. Sin validación de fuentes en respuestas RAG

---

## 📞 Contacto

GitHub: https://github.com/profjcp/mcpsoe
PR activo: #3 (run scripts)
