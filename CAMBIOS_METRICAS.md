# 📊 Cambios Implementados - Sistema de Métricas (v4.0)

## Resumen Ejecutivo

Se ha implementado un **sistema completo de recolección y análisis de métricas** diseñado específicamente para una **investigación de doctorado**. El sistema permite capturar datos cuantitativos (rendimiento) y cualitativos (experiencia) de cada interacción con el RAG.

---

## 🎯 Motivación

Este proyecto es parte de una investigación académica que necesita:
- ✅ **Validación empírica** del desempeño del sistema RAG
- ✅ **Trazabilidad completa** de todas las interacciones
- ✅ **Base de datos** para análisis estadístico riguroso
- ✅ **Transparencia** en cómo el sistema aprende y mejora

---

## 📈 Métricas Cuantitativas Implementadas

### Prometheus Metrics
```
1. queries_total           → Contador de consultas procesadas
2. response_time_seconds   → Histograma de latencias
3. cache_hits_total        → Contador de aciertos en caché
4. errors_total            → Contador de errores
5. cpu_usage_percent       → Gauge de uso de CPU
6. memory_usage_percent    → Gauge de uso de memoria
7. hallucinations_total    → Contador de alucinaciones detectadas
8. response_sentiment      → Gauge de sentimiento promedio
```

**Ubicación en código**: `mcp_server_local.py` líneas 70-80

---

## 🎯 Métricas Cualitativas Implementadas

### User Feedback Metrics
```
1. avg_satisfaction    (1-5) → Calificación de satisfacción
2. avg_clarity        (1-5) → Claridad de respuesta
3. avg_completeness   (1-5) → Completitud de respuesta
4. error_type         (str) → Clasificación de errores
5. comments           (str) → Comentarios libres del usuario
```

### Automatic Detection Metrics
```
6. hallucination_rate (%)  → Detección automática de alucinaciones
7. avg_sentiment      (-1,1)→ Análisis de sentimiento con NLTK
8. query_categories   (dict)→ Categorización automática (6 tipos)
9. response_times     (list)→ Registro histórico de latencias
10. error_types       (dict)→ Agrupación de tipos de errores
```

**Ubicación en código**: 
- Captura: `mcp_server_local.py` líneas 190-280
- Almacenamiento: `qualitative_metrics` dict global

---

## 🔌 Endpoints Nuevos/Modificados

### 1. POST `/ask` (Modificado)
- **Antes**: Solo generaba respuesta
- **Ahora**: Genera respuesta + captura 15 métricas + guarda Q&A

```python
Captura automática:
- Tiempo de procesamiento
- Sentimiento de respuesta
- Presencia de alucinación
- Categoría de consulta
- Cache hit/miss
```

### 2. POST `/feedback` (Nuevo)
- Permite al usuario calificar cada respuesta
- Captura satisfacción, claridad, completitud
- Reporta errores específicos
- Permite comentarios libres

**Payload**:
```json
{
  "question": "¿Cuál es el costo?",
  "response": "El costo es...",
  "satisfaction": 4,
  "clarity": 5,
  "completeness": 4,
  "error_type": "Incomplete",
  "comments": "Faltó información..."
}
```

### 3. GET `/metrics` (Nuevo)
- Retorna agregación de todas las métricas en JSON
- Divide entre quantitative y qualitative
- Incluye distribuciones y promedios

**Respuesta**:
```json
{
  "quantitative": {
    "queries_total": 42.0,
    "cache_hits_total": 18.0,
    ...
  },
  "qualitative": {
    "avg_satisfaction": 4.2,
    "query_categories": {"Costos": 15, ...},
    ...
  }
}
```

### 4. GET `/health` (Nuevo)
- Verifica salud del sistema
- Retorna timestamp

---

## 💻 Cambios en Clientes

### `appclient/app_client.py` (Modificado)
**Nuevas funcionalidades**:
- ✅ Sistema de login/registro con JSON persistence
- ✅ Tracking de tiempos de respuesta (display en UI)
- ✅ Expansor de feedback para cada respuesta
- ✅ Sliders para satisfaction/clarity/completeness
- ✅ Dropdown para error_type
- ✅ Campo de comentarios
- ✅ Envío automático de feedback al servidor

**Cambios técnicos**:
- `load_users()` / `save_users()` → Gestión de usuarios
- `load_histories()` / `save_histories()` → Persistencia de chats
- `st.session_state` → Tracking de sesión de usuario
- Time tracking → `start_time` / `end_time` en tuplas

### `appclient/app_admin.py` (Nuevo - 250+ líneas)
**Dashboard completo con**:
- ✅ Tarjetas de métricas cuantitativas (CPU, Memoria, Queries, Errors)
- ✅ Gráfico de distribución de queries por categoría
- ✅ Gráfico de tipos de error
- ✅ Histograma de satisfacción
- ✅ Tabla de últimos feedbacks
- ✅ Línea temporal de tendencia de satisfacción
- ✅ Sección ejecutiva con KPIs principales
- ✅ Refresh automático/manual

---

## 📁 Nuevos Archivos de Persistencia

```
user_histories.json    → Histórico de chats por usuario
                         {user_id: [{"question": "...", "response": "...", "time": 2.3}, ...]}

users.json            → Base de usuarios con passwords
                         {username: {password_hash: "...", user_id: "...", created: "..."}}

metrics.log           → Registro de operación del servidor
                         [INFO] - Timestamp - Detalles de cada operación

qa_faiss_index.bin    → Índice FAISS de Q&A pairs (persistente)
qa_cache.pkl          → Caché de respuestas guardadas (persistente)
```

---

## 🔍 Detección Automática de Alucinaciones

**Ubicación**: `mcp_server_local.py` función `detect_hallucination()`

```python
def detect_hallucination(response: str, context: str) -> bool:
    """
    Heurística: Si menos del 10% de palabras en la respuesta
    aparecen en el contexto, probablemente es alucinación
    """
    context_words = set(context.lower().split())
    response_words = set(response.lower().split())
    overlap = len(context_words.intersection(response_words))
    return overlap < len(response_words) * 0.1
```

**Mejora futura**: Implementar detección más sofisticada con embedding similarity.

---

## 🏷️ Categorización Automática de Consultas

**Ubicación**: `mcp_server_local.py` función `categorize_query()`

```python
categories = {
    "Costos": ["costo", "precio", "pago", "matrícula", "arancel", "inversión"],
    "Contenidos": ["contenido", "módulo", "curso", "materia", "clase", "programa"],
    "Admisión": ["admisión", "requisito", "inscripción", "documentos", "aplicar"],
    "Horarios": ["horario", "hora", "clase", "fecha", "inicio", "calendario"],
    "Políticas": ["política", "regla", "norma", "reglamento", "procedimiento"],
    "Docentes": ["profesor", "docente", "instructor", "maestro"]
}
```

Permite análisis por tipo de pregunta y mejora continua específica por categoría.

---

## 💡 Análisis de Sentimientos

**Herramienta**: NLTK `SentimentIntensityAnalyzer`

```python
from nltk.sentiment import SentimentIntensityAnalyzer
sia = SentimentIntensityAnalyzer()
sentiment = sia.polarity_scores(full_response)['compound']
# Rango: -1 (muy negativo) a +1 (muy positivo)
```

**Uso**: Detectar si respuestas pueden ser frustrantes (sentimiento negativo).

---

## 🔄 Flujo de Captura de Métrica

### En cada pregunta:

```
1. Usuario hace pregunta
   ↓
2. Incrementar query_counter (Prometheus)
   ↓
3. Categorizar consulta (categorize_query())
   ↓
4. Buscar en FAISS (medir tiempo)
   ↓
5. Generar respuesta LLM (medir tiempo)
   ↓
6. Detectar alucinación (detect_hallucination())
   ↓
7. Analizar sentimiento (SentimentIntensityAnalyzer)
   ↓
8. Registrar: response_time, memory_usage, cpu_usage
   ↓
9. Guardar Q&A pair en caché
   ↓
10. Retornar respuesta al cliente
```

### En feedback:

```
1. Usuario califica (satisfaction, clarity, completeness)
   ↓
2. Selecciona error_type (si aplica)
   ↓
3. Agrega comentarios (opcional)
   ↓
4. Presiona "Enviar Feedback"
   ↓
5. POST /feedback al servidor
   ↓
6. Servidor agrega a qualitative_metrics
   ↓
7. Persiste en memoria para /metrics endpoint
```

---

## 📊 Agregación de Métricas

El endpoint `/metrics` calcula:

```python
# Cuantitativas (de Prometheus)
cpu_usage_percent = psutil.cpu_percent()
memory_usage_percent = psutil.virtual_memory().percent

# Cualitativas (del diccionario)
avg_satisfaction = np.mean(qualitative_metrics["avg_satisfaction"]) if data else 0
hallucination_rate = len([x for x in qualitative_metrics["hallucination_rate"] if x == 1]) / total_queries

# Distribuciones
query_categories = {cat: count for cat, count in qualitative_metrics["query_categories"].items()}
error_types = {err: count for err, count in qualitative_metrics["error_types"].items()}
```

---

## 🎓 Beneficios para la Investigación

| Aspecto | Beneficio |
|---------|----------|
| **Validación** | Datos empíricos para sustentar hipótesis |
| **Reproducibilidad** | Replicar experimentos con mismas métricas |
| **Estadísticas** | Base para análisis de varianza, correlación, etc. |
| **Publicación** | Métricas rigurosas para papers |
| **Comparación** | Benchmark contra otros sistemas RAG |

---

## 🔮 Mejoras Futuras

1. **Base de Datos**: PostgreSQL para histórico ilimitado
2. **Análisis Temporal**: Ver evolución de métricas en el tiempo
3. **Exportación**: PDF/Excel de reportes
4. **Alertas**: Notificación si alucinación_rate > 10%
5. **Benchmarking**: Comparar con otros RAGs o LLMs
6. **GraphRAG**: Análisis relacional de preguntas
7. **A/B Testing**: Comparar diferentes modelos o estrategias

---

## �� Checklist de Implementación

- [x] Métricas Prometheus (Counter, Histogram, Gauge)
- [x] Métricas cualitativas (user feedback)
- [x] Detección de alucinaciones
- [x] Análisis de sentimientos
- [x] Categorización de queries
- [x] Endpoint `/feedback`
- [x] Endpoint `/metrics`
- [x] Dashboard administrativo
- [x] Persistencia JSON
- [x] Logging a archivo
- [x] Cliente con autenticación
- [x] Tracking de tiempos de respuesta
- [x] Integración NLTK con lazy loading

---

**Última actualización**: Enero 20, 2026  
**Versión del Sistema**: 4.0  
**Estado**: ✅ Producción - Completamente Operacional
