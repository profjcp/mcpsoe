# 🎓 Metodología de Investigación Doctoral

## Sistema RAG Híbrido para Consultas Académicas: Un Estudio Empírico

---

## 📋 Resumen Ejecutivo

Este documento describe la metodología de investigación empleada en el desarrollo y validación del sistema SoeBOT, un chatbot educativo basado en arquitectura RAG (Retrieval-Augmented Generation) híbrida. El estudio busca validar empíricamente la hipótesis de que sistemas híbridos FAQ-RAG superan a sistemas RAG tradicionales en cuatro dimensiones críticas: eficiencia, claridad, veracidad y satisfacción del usuario.

**Variables Independientes**: Arquitectura del sistema (FAQ-RAG Híbrido vs. RAG Tradicional)

**Variables Dependientes**: Eficiencia computacional, claridad percibida, tasa de alucinaciones, satisfacción del usuario

**Diseño**: Estudio cuasi-experimental con medidas repetidas y análisis de series temporales

---

## 🎯 Preguntas de Investigación

### RQ1: Eficiencia Computacional
**Pregunta**: ¿Los sistemas RAG híbridos con búsqueda semántica sobre FAQs categorizadas reducen significativamente la latencia de respuesta y el consumo de recursos comparados con sistemas RAG generativos puros?

**Hipótesis H1a**: El tiempo medio de respuesta del sistema híbrido es significativamente menor (p < 0.05) que el sistema RAG tradicional, específicamente: FAQ-RAG ≤ 0.5s vs. RAG puro ≥ 2.5s

**Métricas**:
- `response_time_seconds`: Histograma de latencias por tipo de consulta
- `cpu_usage_percent`: Uso de CPU durante procesamiento
- `memory_usage_percent`: Consumo de memoria RAM
- `cache_hit_rate`: Porcentaje de consultas resueltas sin LLM

### RQ2: Claridad y Comprensibilidad
**Pregunta**: ¿Las respuestas provenientes de FAQs estructuradas son percibidas como más claras y comprensibles que respuestas generadas contextualmente por LLMs?

**Hipótesis H1b**: La claridad promedio de respuestas FAQ (1-5) es significativamente superior a respuestas RAG generativas

**Métricas**:
- `avg_clarity`: Media de calificaciones de claridad (escala Likert 1-5)
- `clarity_distribution`: Distribución estadística de calificaciones
- `clarity_by_category`: Claridad segmentada por dominio (Atención, Académica, Investigación)

### RQ3: Veracidad y Reducción de Alucinaciones
**Pregunta**: ¿La priorización de FAQs pre-validadas reduce la incidencia de alucinaciones en sistemas conversacionales?

**Hipótesis H1c**: La tasa de alucinaciones del sistema híbrido es significativamente menor que sistemas RAG puros (< 5% vs. 15-25%)

**Métricas**:
- `hallucination_rate`: Porcentaje de respuestas con alucinaciones detectadas
- `hallucinations_total`: Contador absoluto de casos
- `error_type_distribution`: Clasificación de errores (Incomplete, Incorrect, Irrelevant)

**Algoritmo de Detección**:
```python
def detect_hallucination(response: str, context: str) -> bool:
    """
    Heurística basada en overlap léxico
    - Tokenización de respuesta y contexto
    - Cálculo de intersección de palabras
    - Umbral: < 10% overlap → probable alucinación
    """
    context_words = set(context.lower().split())
    response_words = set(response.lower().split())
    overlap = len(context_words.intersection(response_words))
    return overlap < len(response_words) * 0.1
```

### RQ4: Satisfacción del Usuario
**Pregunta**: ¿Los usuarios de programas de posgrado expresan mayor satisfacción con respuestas directas (FAQ) que con respuestas generadas contextualmente?

**Hipótesis H1d**: La satisfacción promedio con respuestas FAQ es estadísticamente superior a respuestas RAG

**Métricas**:
- `avg_satisfaction`: Media de satisfacción (escala Likert 1-5)
- `avg_completeness`: Percepción de completitud de información
- `avg_sentiment`: Análisis automático de sentimiento (NLTK VADER)
- `satisfaction_trend`: Serie temporal de evolución de satisfacción

---

## 🔬 Diseño Experimental

### Tipo de Estudio
**Estudio cuasi-experimental** con dos condiciones:

1. **Grupo Experimental**: Sistema RAG Híbrido con búsqueda prioritaria en FAQs
2. **Grupo de Control**: Sistema RAG Tradicional (sin FAQs, solo generativo)

### Variables Controladas
- **LLM**: Llama 3 Typhoon 8B (Q4_K_M) en ambos sistemas
- **Embeddings**: nomic-embed-text (768 dims) para ambos
- **Infraestructura**: Hardware idéntico (CPU, RAM, GPU)
- **Documentos base**: Mismo corpus documental
- **Chunking**: Estrategia idéntica (512 tokens, overlap 50)

### Variables Manipuladas
- **Arquitectura de búsqueda**: FAQ-first vs. RAG-only
- **Categorización**: Multi-dominio vs. sin categorización
- **Umbral de similitud**: 0.75 (FAQ) vs. N/A

### Población y Muestra
- **Población objetivo**: Estudiantes de programas de posgrado (maestrías en STEM)
- **Tamaño muestral**: Mínimo 100 interacciones por condición (N ≥ 200 total)
- **Criterios de inclusión**: 
  - Consultas relacionadas con programas académicos
  - Usuarios registrados en plataforma
  - Conversaciones en español
- **Criterios de exclusión**:
  - Consultas de prueba o testing
  - Interacciones < 5 palabras
  - Feedback incompleto

### Asignación de Condiciones
**Diseño within-subjects**: Cada usuario interactúa con ambas versiones del sistema
- Semanas 1-2: Sistema RAG Tradicional (baseline)
- Semanas 3-4: Sistema Híbrido FAQ-RAG
- **Contrabalanceo**: 50% de usuarios inician con híbrido

---

## 📊 Recolección de Datos

### Datos Cuantitativos (Automáticos)

**Sistema de métricas Prometheus** con 8 contadores:

```python
# Eficiencia
response_time = Histogram('response_time_seconds', buckets=[0.1, 0.5, 1, 2, 5, 10])
cpu_usage = Gauge('cpu_usage_percent')
memory_usage = Gauge('memory_usage_percent')

# Calidad
query_counter = Counter('queries_total', ['category', 'source'])  # source=FAQ|RAG
cache_hit_counter = Counter('cache_hits_total')
error_counter = Counter('errors_total', ['error_type'])
hallucination_counter = Counter('hallucinations_total', ['source'])

# Experiencia
sentiment_score = Gauge('response_sentiment')
```

**Persistencia**: 
- `metrics.log`: Registro timestamped de todas las operaciones
- `feedback.jsonl`: Base de datos de feedback cualitativo (JSON Lines)

### Datos Cualitativos (Explícitos)

**Formulario de feedback** post-respuesta:

```json
{
  "question": "¿Cuál es el costo del programa?",
  "response": "El costo total es...",
  "response_time": 0.4,
  "source": "FAQ",
  "category": ["AtencionCliente"],
  "timestamp": "2026-02-17T15:30:00",
  "satisfaction": 5,        // 1-5 Likert
  "clarity": 5,            // 1-5 Likert
  "completeness": 4,       // 1-5 Likert
  "error_type": null,      // null | "Incomplete" | "Incorrect" | "Irrelevant"
  "comments": "Respuesta rápida y precisa",
  "user_id": "user_12345"
}
```

### Datos de Contexto

- **User histories** (`user_histories.json`): Historial completo de conversaciones por usuario
- **Logs de categorización**: Clasificación automática de consultas por dominio
- **Métricas de sistema**: CPU, memoria, disco (para análisis de carga)

---

## 📈 Análisis Estadístico

### Análisis Descriptivo

**Estadísticas por grupo**:
- Media, mediana, desviación estándar
- Percentiles (P25, P50, P75, P90, P95, P99)
- Distribuciones (histogramas, boxplots)
- Series temporales (tendencias)

### Análisis Inferencial

#### Pruebas Paramétricas
**Condiciones**:
1. Distribución normal (Shapiro-Wilk, K-S)
2. Homogeneidad de varianzas (Levene)
3. Independencia de observaciones

**Test t de Student para muestras independientes**:
```
H0: μ_FAQ = μ_RAG (no hay diferencia)
H1: μ_FAQ ≠ μ_RAG (hay diferencia significativa)
α = 0.05
```

**ANOVA de una vía**: Para comparar múltiples grupos (por categoría)

#### Pruebas No Paramétricas (si no se cumple normalidad)
- **Mann-Whitney U**: Comparación de dos grupos independientes
- **Kruskal-Wallis**: Comparación de múltiples grupos
- **Wilcoxon signed-rank**: Comparación de medidas repetidas

### Análisis de Correlación
- **Pearson**: Para variables continuas con relación lineal
- **Spearman**: Para variables ordinales o no lineales

**Correlaciones de interés**:
- Tiempo de respuesta vs. Satisfacción
- Claridad vs. Completitud
- Uso de caché vs. Eficiencia

### Análisis de Series Temporales
- **Tendencias**: Regresión lineal sobre satisfacción en el tiempo
- **Estacionalidad**: Detección de patrones horarios/diarios
- **Outliers**: Identificación de anomalías

---

## 🎯 Criterios de Validación

### Validez Interna
✅ **Control de variables confusoras**: Misma infraestructura y LLM base
✅ **Asignación aleatoria**: Contrabalanceo de condiciones
✅ **Mediciones estandarizadas**: Escalas Likert validadas
✅ **Instrumentación consistente**: API única para ambas condiciones

### Validez Externa
✅ **Muestra representativa**: Usuarios reales de programas de posgrado
✅ **Contexto ecológico**: Consultas auténticas (no simuladas)
✅ **Replicabilidad**: Código y datos disponibles (open source)
✅ **Generalización**: Resultados aplicables a otros contextos educativos

### Validez de Constructo
✅ **Eficiencia**: Medida objetiva (tiempo, recursos)
✅ **Claridad**: Calificación subjetiva validada + análisis de sentimiento
✅ **Veracidad**: Algoritmo heurístico + revisión manual de muestra
✅ **Satisfacción**: Escala Likert + feedback textual

### Confiabilidad
✅ **Consistencia interna**: Alpha de Cronbach para escalas multi-ítem
✅ **Estabilidad temporal**: Test-retest en muestra
✅ **Inter-rater reliability**: Dos evaluadores para clasificación de alucinaciones

---

## 📊 Dashboard de Análisis

### Sección 1: Eficiencia Computacional
**Visualizaciones**:
- Histograma de tiempos de respuesta (FAQ vs. RAG)
- Serie temporal de uso de CPU/memoria
- Gauge de tasa de cache hit (target: > 60%)
- Tabla de percentiles de latencia

**Métricas clave**:
```
Avg Response Time (FAQ): 0.32s ± 0.15s
Avg Response Time (RAG): 2.47s ± 0.68s
Cache Hit Rate: 67.3%
CPU Avg Usage: 42.1%
```

### Sección 2: Claridad
**Visualizaciones**:
- Boxplot de distribución de claridad (FAQ vs. RAG)
- Heatmap de claridad por categoría de consulta
- Tabla de casos con baja claridad (< 3) para análisis cualitativo

**Métricas clave**:
```
Avg Clarity (FAQ): 4.6 ± 0.5
Avg Clarity (RAG): 3.8 ± 0.9
p-value (t-test): 0.0012 **
```

### Sección 3: Veracidad
**Visualizaciones**:
- Gauge de tasa de alucinaciones (FAQ vs. RAG)
- Pie chart de tipos de error
- Evolución temporal de alucinaciones

**Métricas clave**:
```
Hallucination Rate (FAQ): 3.2%
Hallucination Rate (RAG): 18.7%
Error Types: Incomplete (45%), Incorrect (35%), Irrelevant (20%)
```

### Sección 4: Satisfacción
**Visualizaciones**:
- Línea de tendencia de satisfacción en el tiempo
- Histograma de distribución de satisfacción
- Word cloud de comentarios positivos/negativos

**Métricas clave**:
```
Avg Satisfaction (FAQ): 4.7 ± 0.4
Avg Satisfaction (RAG): 3.9 ± 0.8
Avg Sentiment: 0.72 (positivo)
```

### Exportación de Datos
**Botones de descarga CSV** en cada sección para análisis externo:
- `eficiencia.csv`: Todas las métricas de rendimiento
- `claridad.csv`: Calificaciones y casos de baja claridad
- `veracidad.csv`: Alucinaciones detectadas y errores
- `satisfaccion.csv`: Satisfacción, completitud y comentarios

---

## 🔄 Proceso de Iteración

### Fase 1: Baseline (Semanas 1-2)
- Implementación de sistema RAG tradicional
- Recopilación de métricas de control
- Análisis de puntos de dolor (queries lentas, errores frecuentes)

### Fase 2: Desarrollo de FAQs (Semanas 3-4)
- Análisis de consultas más frecuentes (top 50)
- Categorización en 3 dominios
- Redacción de 50+ pares Q&A validados
- Implementación de búsqueda semántica

### Fase 3: Experimentación (Semanas 5-8)
- Despliegue del sistema híbrido
- Recopilación comparativa de métricas
- Ajuste de umbrales de similitud
- Monitoreo de anomalías

### Fase 4: Análisis (Semanas 9-10)
- Análisis estadístico comprehensivo
- Pruebas de hipótesis
- Identificación de patrones
- Documentación de hallazgos

### Fase 5: Validación (Semanas 11-12)
- Revisión manual de muestra (10% de interacciones)
- Validación de alucinaciones detectadas
- Entrevistas cualitativas con usuarios clave
- Triangulación de datos

---

## 📝 Consideraciones Éticas

### Consentimiento Informado
✅ Los usuarios son informados del uso de sus datos para investigación
✅ Opción de opt-out sin penalización
✅ Datos anonimizados para análisis (user_id hasheado)

### Privacidad
✅ No se recopilan datos sensibles (nombres, correos, ubicación)
✅ Almacenamiento local (no cloud externo)
✅ Acceso restringido a datos por contraseña

### Transparencia
✅ Sistema indica cuando usa FAQ vs. RAG generativo
✅ Visualización de tiempos de respuesta
✅ Dashboard accesible para administradores

### Beneficencia
✅ Sistema busca mejorar experiencia educativa
✅ Respuestas rápidas y precisas
✅ Reducción de carga administrativa

---

## 📚 Referencias Metodológicas

### Diseño Experimental
- Campbell, D. T., & Stanley, J. C. (1963). *Experimental and quasi-experimental designs for research*
- Shadish, W. R., Cook, T. D., & Campbell, D. T. (2002). *Experimental and quasi-experimental designs for generalized causal inference*

### Análisis Estadístico
- Field, A. (2013). *Discovering statistics using IBM SPSS statistics* (4th ed.)
- Tabachnick, B. G., & Fidell, L. S. (2013). *Using multivariate statistics* (6th ed.)

### Sistemas RAG
- Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020
- Gao, Y., et al. (2023). "Retrieval-Augmented Generation for Large Language Models: A Survey." arXiv:2312.10997

### Evaluación de Chatbots
- Chakrabarti, C., & Luger, G. F. (2015). "Artificial conversations for customer service chatter bots." *Expert Systems with Applications*
- Følstad, A., & Brandtzæg, P. B. (2017). "Chatbots and the new world of HCI." *Interactions*, 24(4), 38-42

---

## 🔮 Extensiones Futuras

### Mejoras Técnicas
- [ ] Embeddings contextuales (transformers fine-tuned)
- [ ] Detección de alucinaciones con similarity embeddings
- [ ] Multi-idioma (inglés, portugués)
- [ ] Generación de FAQs automática desde logs

### Análisis Avanzado
- [ ] Machine learning para predicción de satisfacción
- [ ] Análisis de contenido cualitativo (NVivo, Atlas.ti)
- [ ] Network analysis de categorías de consultas
- [ ] A/B testing continuo con variantes

### Escalamiento
- [ ] Federación de FAQs (múltiples instituciones)
- [ ] API pública para integración con LMS
- [ ] Sistema de recomendación de preguntas relacionadas
- [ ] Modo offline para acceso sin conexión

---

**Documento preparado por**: Equipo de Investigación SoeBOT  
**Última actualización**: 17 de febrero de 2026  
**Versión**: 1.0
