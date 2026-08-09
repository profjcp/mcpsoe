# 📋 Plan de Implementación — RAG Académico Seguro (SoeBOT)

> **Propósito:** Documentar el plan paso a paso para implementar el RAG académico preciso y seguro.
> **Uso:** Este documento sirve como referencia para retomar el trabajo en sesiones futuras sin perder contexto.
> **Última actualización:** (fecha de creación)

---

## 🧭 Contexto del Proyecto

- **Proyecto:** SoeBOT — Asistente académico de posgrado (UPG).
- **Versión actual:** 2.0 (Pipeline Multiagente).
- **Arquitectura:** `MultiAgentOrchestrator` con routing `GUIDANCE → FAQ → CACHE → RAG_DOC/GRAPH_RAG`.
- **Agentes:** `FAQAgent`, `DocRAGAgent`, `GraphRAGAgent`.
- **Búsqueda:** FAISS vectorial puro (`IndexFlatL2`).
- **Modelos:** Ollama (`llama-3-typhoon-v1.5-8b-instruct-q4_k_m` para LLM, `nomic-embed-text` para embeddings).
- **Servidor:** FastAPI (`mcp_server_local.py`, puerto 9000).
- **Evaluación:** RAGAs + benchmark T1.

---

## 🎯 Objetivo del Plan

Implementar un RAG académico que garantice:
1. **Seguridad / Control de acceso** — el modelo jamás accede a información no autorizada para el perfil del usuario.
2. **Precisión** — recuperar exactamente el fragmento normativo correcto (sin ruido).
3. **Cero alucinaciones** — respuestas estrictamente basadas en el contexto recuperado y citadas.
4. **Control de calidad** — auditar la respuesta antes de mostrarla al usuario.

---

## 🔍 Análisis de Factibilidad (Estado actual vs. Plan)

| Etapa | Plan propuesto | Estado actual en código | Acción requerida |
|-------|----------------|-------------------------|------------------|
| Entrada | Query Rewriter/Clarifier | ⚠️ `needs_guidance()` heurístico en `mcp_server_local.py` | Añadir LLM rewriting + aclaración interactiva de doble turno |
| Búsqueda | Metadata Pre-filter | ❌ No existe; FAISS global | Enriquecer chunks con metadatos + filtrar por perfil |
| Recuperación | Hybrid (FAISS+BM25) + Reranking | ❌ Solo vectorial FAISS | Añadir BM25 + EnsembleRetriever + Reranker Cross-Encoder |
| Generación | Strict Grounded Prompt | ⚠️ Template básico en `_build_chain()` | Reforzar con cita exacta de artículo + cero conocimiento previo + omisión confidencial |
| Validación | Hallucination Grader | ⚠️ `detect_hallucination()` heurística (solo métricas, no bloquea) | Añadir grader LLM que descarte respuestas no respaldadas |

**Veredicto:** El plan es **ALTAMENTE FACTIBLE**. El proyecto ya tiene ~40% del plan de forma parcial. Se integra en las clases existentes sin reescribir la arquitectura.

---

## 📦 Plan de Implementación Priorizado

### 🔴 FASE 1 — Fundamentos de Seguridad y Grounding (PRIMERO)

#### Paso 1.1: Enriquecer ingesta con metadatos + Control de Acceso
- **Archivos afectados:**
  - `preprocess.py` — leer múltiples documentos de `documentos/`, asignar metadatos (`programa`, `categoria`, `nivel_acceso`, `articulo`, `gestion`), guardar chunks como `{text, metadata}`.
  - `agents/rag_doc_agent.py` — aceptar filtro de metadatos y aplicarlo **antes** de la búsqueda FAISS (pre-filtering).
  - `agents/graph_rag_agent.py` — misma lógica de pre-filtrado.
  - `orchestrator/router.py` — propagar perfil de usuario al routing.
  - `mcp_server_local.py` — usar `user_id` del `AskRequest` para determinar `nivel_acceso` y programa.
- **Importancia:** 🔥 **CRÍTICA** — Base de seguridad. Habilita pasos 2 y 5.
- **Riesgos:** Requiere re-generar índice (`preprocess.py`) y migrar `chunks.pkl` al nuevo formato (cambio de esquema de datos).

#### Paso 1.2: Prompt de Grounding Estricto (Zero Tolerancia a Alucinaciones)
- **Archivos afectados:**
  - `mcp_server_local.py` — reforzar `_build_chain()` con reglas inquebrantables del plan:
    1. Responder ÚNICA Y EXCLUSIVAMENTE basado en el contexto.
    2. Si no está en el contexto → "No dispongo de esa información en los reglamentos vigentes. Por favor, acude a la Jefatura Académica."
    3. NUNCA asumir, deducir ni usar conocimiento previo de otras universidades.
    4. Citar el artículo o documento exacto.
    5. Omitir información confidencial o no autorizada.
  - `rag.py` — si se mantiene como fallback.
- **Importancia:** 🔥 **CRÍTICA** — Reduce alucinaciones con mínimo esfuerzo.
- **Riesgos:** Ninguno de infraestructura.

---

### 🟠 FASE 2 — Precisión de Recuperación

#### Paso 2.1: Búsqueda Híbrida (Vectorial + BM25)
- **Archivos afectados:**
  - `requirements.txt` — añadir `rank_bm25`, `langchain-community` (si falta).
  - Nuevo módulo `retrieval/hybrid_retriever.py` — combinar `BM25Retriever` + FAISS con `EnsembleRetriever`.
  - `agents/rag_doc_agent.py` — usar `HybridRetriever` en lugar de FAISS puro.
- **Importancia:** 🟠 **ALTA** — Mejora recuperación de términos exactos (códigos, resoluciones, fechas).

#### Paso 2.2: Reranker (Cross-Encoder)
- **Archivos afectados:**
  - `requirements.txt` — añadir `sentence-transformers` (BGE-Reranker) o cliente Cohere.
  - `retrieval/hybrid_retriever.py` — aplicar reranker a top-10 → top-3.
  - `agents/rag_doc_agent.py` — consumir los top-3 rerankeados.
- **Importancia:** 🟠 **ALTA** — Asegura que solo lleguen al LLM los fragmentos más exactos.

---

### 🟡 FASE 3 — Control de Calidad y Entrada

#### Paso 3.1: Agente Evaluador de Alucinaciones (Hallucination Grader)
- **Archivos afectados:**
  - Nuevo módulo `agents/hallucination_grader.py` — LLM secundario que evalúa respuesta vs. contexto (booleano True/False).
  - `mcp_server_local.py` — en `stream_rag_doc()`, si el grader devuelve False, **descartar la respuesta** y enviar mensaje seguro de contingencia.
  - Sustituir/mejorar `detect_hallucination()` heurístico.
- **Importancia:** 🟡 **MEDIA-ALTA** — Red de seguridad final.
- **Riesgos:** Incrementa latencia (una llamada LLM extra) y coste de tokens.

#### Paso 3.2: Query Rewriter / Aclarador Interactivo
- **Archivos afectados:**
  - Nuevo módulo `agents/query_rewriter.py` — reescribe consultas claras para búsqueda técnica.
  - `mcp_server_local.py` — mejorar `needs_guidance()` y añadir aclaración interactiva de doble turno (preguntar programa/modalidad si falta contexto).
  - `orchestrator/router.py` — integrar rewriter antes de la fase de recuperación.
- **Importancia:** 🟡 **MEDIA** — Refina la entrada. Complementa el grounding.

---

## 📊 Orden de Resolución Recomendado

```
1. FASE 1.2 (Prompt estricto)      ← Menor esfuerzo, alto impacto inmediato
2. FASE 1.1 (Metadatos + acceso)   ← Base de seguridad, habilita pasos 2 y 5
3. FASE 2.1 (Búsqueda híbrida)     ← Mejora recuperación
4. FASE 2.2 (Reranker)             ← Precisión final de recuperación
5. FASE 3.1 (Grader alucinación)   ← Red de seguridad final
6. FASE 3.2 (Query rewriter)       ← Refinamiento de entrada
```

**Lógica del orden:** Paso 1.2 es rápido y da valor inmediato. Paso 1.1 es la base estructural. Luego se mejora recuperación (Fase 2) y finalmente control de calidad (Fase 3). Query Rewriter queda al final porque depende de buena recuperación y grounding.

---

## ⚠️ Dependencias y Riesgos Globales

1. **Paso 1.1** requiere re-generar el índice (`preprocess.py`) y **migrar `chunks.pkl`** al nuevo formato con metadatos → cambio de esquema de datos.
2. **Paso 2.1/2.2** requieren verificar/añadir dependencias en `requirements.txt` e instalarlas en `venmcp/`.
3. **Paso 3.1** incrementa latencia y coste de tokens (una llamada LLM extra por respuesta).
4. **Ollama** debe estar corriendo para los modelos (`llama-3-typhoon...` y `nomic-embed-text`).

---

## ✅ Estado de Progreso (Checklist)

- [ ] **FASE 1.2** — Prompt de Grounding Estricto
- [ ] **FASE 1.1** — Metadatos + Control de Acceso
- [ ] **FASE 2.1** — Búsqueda Híbrida (BM25 + FAISS)
- [ ] **FASE 2.2** — Reranker Cross-Encoder
- [ ] **FASE 3.1** — Hallucination Grader
- [ ] **FASE 3.2** — Query Rewriter / Aclarador

---

## 📁 Archivos Relevantes del Proyecto

| Archivo | Rol |
|---------|-----|
| `preprocess.py` | Genera chunks + índice FAISS + grafo |
| `rag.py` | RAG agentic legacy (fallback) |
| `agents/rag_doc_agent.py` | RAG documental (Sprint 1) |
| `agents/graph_rag_agent.py` | GraphRAG (Sprint 2) |
| `agents/faq_agent.py` | FAQ semántico |
| `orchestrator/router.py` | MultiAgentOrchestrator |
| `mcp_server_local.py` | Servidor FastAPI + prompts + métricas |
| `shared_client.py` | Cliente MCP |
| `mcp_lib/server.py` | SDK cliente MCP |
| `main.py` | Endpoint FastAPI simplificado (legacy) |
| `documentos/` | Documentos fuente (FAQ, reglamentos) |
| `requirements.txt` | Dependencias |

---

## 🔜 Próximos Pasos (Retomar aquí)

Al retomar el trabajo:
1. Verificar que este documento esté actualizado con el progreso real.
2. Comenzar por **FASE 1.2 (Prompt estricto)** — es el de menor esfuerzo y mayor impacto inmediato.
3. Confirmar con el usuario si se avanza a FASE 1.1 (Metadatos) después.
