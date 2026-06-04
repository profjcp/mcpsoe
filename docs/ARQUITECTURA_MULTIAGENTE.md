# Arquitectura Multiagente SoeBOT v2.0

## Resumen

SoeBOT v2.0 introduce una **arquitectura multiagente** que mejora la precisión y reduce falsos positivos en consultas académicas, especialmente en tesis e investigación.

## Migración de mono-agente a multiagente

### Antes (v1.x)
```
[Pregunta] -> [FAQ] -> [RAG] -> [LLM]
```
- Un único pipeline sin routing inteligente
- Posibles falsos positivos cuando FAQs no relacionadas coincidían
- Cache contaminado con respuestas incorrectas para consultas de tesis

### Ahora (v2.0)
```
[Pregunta] -> [Router] -> [FAQAgent] / [DocRAGAgent] -> [Cache] -> [LLM]
                   |
              [Guardrails]
```
- Routing inteligente pre-LLM basado en categorías
- Agentes especializados para cada dominio
- Guardrails léxicos para bloquear falsos positivos

## Componentes Nuevos

### 1. Router (`orchestrator/router.py`)
Encargado de analizar la pregunta y determinar qué agente debe manejarla.

```python
class MultiAgentOrchestrator:
    def route_pre_llm(self, question: str, user_id: str) -> RoutingDecision:
        """
        Analiza la pregunta y retorna:
        - mode: GUIDANCE | FAQ | CACHE | RAG_DOC
        - source: Origen de la respuesta
        - confidence: Nivel de confianza (0.0-1.0)
        - categories: Categorías detectadas
        """
```

**Flujo de decisión:**
1. **GUIDANCE**: Pregunta vaga ("ayuda", "info", etc.)
2. **FAQ**: Coincidencia exacta en FAQs con threshold > 0.82
3. **CACHE**: Coincidencia exacta en caché Q&A
4. **RAG_DOC**: Búsqueda en documentos académicos

### 2. FAQAgent (`agents/faq_agent.py`)
Agente especializado en respuestas de FAQs con guardrails.

```python
class FAQAgent:
    def __init__(self, threshold: float = 0.82, min_token_overlap: int = 2):
        # threshold: Similitud mínima para aceptar respuesta FAQ
        # min_token_overlap: Mínimo de tokens compartidos para validar relevancia
```

**Guardrails implementados:**
- Normalización léxica (minúsculas, sin acentos)
- Filtrado por categorías (evitar match entre dominios diferentes)
- Restricciones para tesis/defensa (fuertes cuando categoría es "Academica" o "Investigacion")

### 3. DocRAGAgent (`agents/rag_doc_agent.py`)
Agente para búsqueda en documentos académicos.

```python
class DocRAGAgent:
    def retrieve(self, question: str, top_k: int = 5) -> list[str]:
        # Busca en FAISS con embeddings
        # Retorna top-k chunks relevantes
```

## Diagrama de Arquitectura

```
                    ┌──────────────────┐
                    │    PREGUNTA    │
                    └────────┬───────┘
                             │
                             v
                    ┌──────────────────┐
                    │  MULTIAGENT     │
                    │    ROUTER       │
                    └────────┬───────┘
                             │
            ┌───────────────┼───────────────┐
            │               │               │
            v               v               v
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │  GUIDANCE │  │ FAQAgent │  │DocRAGAgent│
      │          │  │ (FAQ)   │  │ (Docs)   │
      └──────────┘  └────┬────┘  └──��─┬────┘
                          │           │
           ┌───────────────┼───────────┤
           v               v           v
     ┌──────────┐   ┌──────────┐  ┌──────────┐
     │  CACHE  │   │ MATCH?  │  │  FAISS  │
     │  (Q&A) │   │ (Sim>0.82)│ │ (Chunks)│
     └──────────┘   └────┬────┘  └────┬────┘
                         │           │
                         v           v
                   ┌──────────────────┐
                   │      LLM        │
                   │  (Ollama)       │
                   └────────┬───────┘
                            │
                            v
                   ┌──────────────────┐
                   │    RESPUESTA     │
                   └──────────────────┘
```

## Categorías Soportadas

| Categoría | Dominio | Ejemplos |
|-----------|--------|----------|
| **AtencionCliente** | Inscripciones, pagos, Moodle | "¿Cómo me inscribo?", "¿Cuándo pagan?" |
| **Academica** | Programas, módulos, docentes | "¿Qué módulos hay?", "¿Quién enseña?" |
| **Investigacion** | Tesis, tutores, defensa | "¿Cómo obtengo tutor?", "¿Qué es la defensa?" |
| **Otro** | Fuera de dominio | Cualquier otra pregunta |

## Guardrails para Tesis/Investigación

Para evitar que consultas sobre tesis devuelvan respuestas de FAQs no relacionadas (ej: "¿Dónde queda SOE?" para "¿Cómo defiendo mi tesis?"):

1. **Threshold elevado**: 0.82 (vs 0.75 anterior)
2. **Revisión de categorías**: Si categoría es "Academica" o "Investigacion", se descartan matches de "AtencionCliente"
3. **Bypass de caché**: Para categorías sensibles, se fuerza siempre RAG_DOC si la respuesta cacheada no tiene contexto de documentos

## Métricas y Logging

Se preservan todas las métricas existentes y se añade:

| Métrica | Descripción |
|--------|------------|
| `route_mode` | Modo de routing usado (GUIDANCE/FAQ/CACHE/RAG_DOC) |
| `route_confidence` | Confianza del router (0.0-1.0) |
| `guardrail_triggered` | Si algún guardrail fue activado |

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `mcp_server_local.py` | +355 líneas: routing, lifespan, cache bypass |
| `agents/faq_agent.py` | +58 líneas: guardrails, threshold, categorización |
| `orchestrator/router.py` | Nuevo: clase MultiAgentOrchestrator |
| `agents/rag_doc_agent.py` | Nuevo: clase DocRAGAgent |

## Próximos Pasos (Sprint 2)

- [ ] GraphRAG para relaciones entre documentos
- [ ] Validación de respuestas generadas con fuentes
- [ ] Feedback loop para reentrenamiento
- [ ] Dashboard de diagnóstico de agentes

---

*Última actualización: 2026-06-03*
*Versión: 2.0-Sprint1*
