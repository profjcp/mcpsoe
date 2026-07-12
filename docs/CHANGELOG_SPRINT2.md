# Changelog Sprint 2 — Routing, Observabilidad y UX Admin

## Resumen
Este documento consolida los cambios implementados en Sprint 2 para mejorar:
- trazabilidad del enrutamiento multiagente,
- observabilidad de fuentes/métricas en backend,
- visibilidad de metadatos en cliente,
- panel administrativo para análisis de routing,
- usabilidad de navegación en pestañas del admin.

---

## 1) Enrutamiento multiagente (backend)

### Archivo
- `orchestrator/router.py`

### Cambios principales
- Se extendió `routing_trace` con campos de observabilidad:
  - `route_version`
  - `selected_mode`
  - `decision_reason`
  - `fallbacks_applied`
  - `decision_timing_ms`
- Se añadió mayor detalle temporal por fase de decisión para mejorar diagnósticos.
- Se mantuvo compatibilidad con el flujo existente `GUIDANCE -> FAQ -> CACHE -> RAG_DOC` y rutas relacionadas.

### Beneficio
- Permite auditar por qué se eligió cada ruta de respuesta.
- Facilita análisis de calidad de enrutamiento por sesión y por usuario.

---

## 2) Métricas y observabilidad (backend)

### Archivo
- `mcp_server_local.py`

### Cambios principales
- Se normalizó el conteo de fuentes para incluir explícitamente `GRAPH_RAG`.
- El endpoint `/metrics` ahora incluye agregados de observabilidad:
  - `source_counts`
  - `graph_rag_total`
  - `graph_rag_rate_percent`
  - `routing_trace_present_total`
  - `routing_trace_coverage_percent`
- Se preservó la compatibilidad con métricas previas cuantitativas/cualitativas.

### Beneficio
- Visibilidad operativa directa de adopción de `GRAPH_RAG`.
- Control de cobertura de trazas para asegurar auditabilidad.

---

## 3) Cliente (UX y trazabilidad de respuesta)

### Archivo
- `appclient/app_client.py`

### Cambios principales
- Se incorporó visualización no invasiva de metadatos por respuesta:
  - modo/fuente,
  - confianza,
  - fuentes,
  - `routing_trace`,
  - `timing_ms`.
- Se mejoró compatibilidad de historial:
  - formato legado (tuplas/listas),
  - formato nuevo (dict con `meta`).
- Se mantiene continuidad de experiencia para usuarios históricos.

### Beneficio
- Mejora la transparencia de cómo responde el sistema.
- Reduce fricción en migraciones de formato de historial.

---

## 4) Dashboard administrativo (routing observability)

### Archivo
- `appclient/app_admin.py`

### Cambios principales
- Se añadió pestaña de observabilidad de routing con:
  - distribución por `source`,
  - `% GRAPH_RAG`,
  - trazas recientes,
  - distribución de `decision_reason`.
- Mejora UX de tabs:
  - scroll horizontal en tablist,
  - etiquetas acortadas para que todas las pestañas sean visibles:
    - `📌 Res.`, `📈 Cuant.`, `✨ Cual.`, `👤 Usrs`, `🧭 Routing`, `🧮 Método`, `🗂️ Datos`.

### Beneficio
- Mayor legibilidad en pantallas medianas/pequeñas.
- Navegación más clara y estable en entornos con múltiples pestañas.

---

## 5) Evaluación y documentación

### Archivos
- `evaluation/README.md`
- `evaluation/ragas_worker.py`
- `evaluation/eval_ragas_batch.py`
- `PROJECT_STATUS.md`
- `TODO.md`

### Cambios principales
- Actualización del flujo de evaluación para Sprint 2:
  - enfoque streaming,
  - mapeo canónico,
  - uso de logs para inferencia de tipo/fuente.
- Actualización de estado y checklist de avance.

### Beneficio
- Reproducibilidad y trazabilidad del proceso de evaluación experimental.
- Mejor alineación con objetivos de validación de tesis.

---

## Notas de publicación
- Este sprint se publica excluyendo artefactos locales/binarios (`*.pkl`, `*.bin`, `__pycache__`, logs).
- Se prioriza código funcional, documentación y scripts de evaluación.
