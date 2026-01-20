# SoeBOT - Sistema RAG Inteligente con Métricas de Investigación

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31.1-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Descripción General

**SoeBOT** es un sistema completo de Generación Aumentada por Recuperación (RAG) diseñado para automatizar respuestas a preguntas frecuentes de un programa de maestría. El sistema integra:

- 🤖 **LLM Avanzado**: Ollama con modelo Llama 3 Typhoon optimizado para precisión
- 📊 **Métricas Investigativas**: Sistema comprehensivo de tracking cuantitativo y cualitativo
- 💬 **Interfaz Chat**: Cliente Streamlit con autenticación de usuarios
- 📈 **Dashboard Administrativo**: Visualización de métricas en tiempo real
- 🔍 **Búsqueda Semántica**: FAISS para recuperación inteligente de documentos
- 💾 **Caché Inteligente**: Aprendizaje continuo mediante Q&A pairs
- 🧠 **Memoria Conversacional**: Sistema guarda cada par pregunta-respuesta para aprendizaje futuro

---

## 🎯 ¿Por Qué Se Agregaron las Métricas?

### Contexto: Investigación de Doctorado

Este proyecto forma parte de una **investigación de doctorado** que busca validar la efectividad de un sistema RAG en contextos educativos específicos. Por ello, se requería:

1. **Recolección de Datos Cuantitativos**: Para medir rendimiento técnico y eficiencia
2. **Recolección de Datos Cualitativos**: Para evaluar la experiencia del usuario y la calidad de respuestas
3. **Trazabilidad Completa**: Para poder auditar y analizar cada interacción
4. **Análisis Estadístico**: Para extraer insights sobre patrones de uso y satisfacción

### Métricas Implementadas

#### 📊 Métricas Cuantitativas (Prometheus)

```
✅ cpu_usage_percent          - Uso de CPU en tiempo real
✅ memory_usage_percent       - Consumo de memoria del servidor
✅ queries_total              - Total de consultas procesadas
✅ cache_hits_total           - Consultas respondidas desde caché
✅ errors_total               - Cantidad de errores detectados
✅ hallucinations_total       - Alucinaciones detectadas en respuestas
✅ response_time_seconds      - Histograma de tiempos de respuesta
```

#### 🎯 Métricas Cualitativas Personalizadas

```
✅ avg_satisfaction (1-5)     - Satisfacción promedio del usuario
✅ avg_clarity (1-5)          - Claridad promedio de respuestas
✅ avg_completeness (1-5)     - Completitud promedio de respuestas
✅ hallucination_rate         - Tasa de alucinaciones (%)
✅ avg_sentiment              - Sentimiento promedio de respuestas (NLTK)
✅ query_categories           - Categorización automática de preguntas
✅ error_types                - Clasificación de tipos de errores
✅ response_times             - Registro temporal de latencias
```

---

## 💡 Beneficios de las Métricas

### Para la Investigación
- 📈 **Validación Empírica**: Datos reales de uso para sustentar conclusiones
- 🔬 **Análisis Estadístico**: Base para estudios de correlación y causalidad
- 📋 **Reproducibilidad**: Capacidad de replicar experimentos y resultados
- 🎓 **Publicabilidad**: Métricas rigurosas para papers académicos

### Para la Optimización del Sistema
- ⚡ **Performance Tuning**: Identificar cuellos de botella (response times, CPU)
- 🎯 **Mejora Iterativa**: Datos basados en evidencia para ajustes del modelo
- 🐛 **Detección de Anomalías**: Identificación automática de alucinaciones
- 💰 **Eficiencia Operacional**: Monitoreo de uso de recursos

### Para el Usuario
- ⏱️ **Visibilidad**: Ver tiempo de procesamiento de cada respuesta
- 😊 **Feedback Valorado**: Sistema de calificación que valida su experiencia
- 📊 **Transparencia**: Dashboard que muestra cómo mejora el sistema

### Para la Institución
- 📊 **Análisis de Demanda**: Entender qué preguntas son más frecuentes
- 🎓 **Mejora Académica**: Identificar tópicos que necesitan clarificación
- 💼 **ROI Visible**: Datos que justifican inversión en IA
- 🔄 **Iteración Basada en Datos**: Mejoras continuas documentadas

---

## 🚀 Inicio Rápido

### Paso 1: Preparar Entorno

```bash
# Clonar repositorio y navegar
cd /home/aisoe/mcpsoe

# Verificar prerrequisitos
ollama serve                    # En otra terminal
redis-server                    # En otra terminal
```

### Paso 2: Ejecutar Sistema Completo

```bash
# Instalación automática y ejecución
chmod +x run.sh
./run.sh                        # Cliente solo
./run.sh --admin               # Con dashboard de métricas
```

### Paso 3: Acceder Interfaz

```
💬 Cliente:           http://localhost:8501
📊 Dashboard Admin:   http://localhost:8502
🤖 API FastAPI:       http://localhost:9000
```

---

## 📦 Requisitos Previos

### Software Necesario
- **Python 3.12+** - Lenguaje principal
- **Ollama** - Servicio de LLM local
- **Redis** - Caché distribuido
- **Git** - Control de versiones

### Modelos Ollama
```bash
ollama pull promptnow/llama-3-typhoon-v1.5-8b-instruct-q4_k_m  # LLM principal
ollama pull nomic-embed-text                                     # Embeddings
```

### Dependencias Python
Ver [requirements.txt](requirements.txt) - Se instalan automáticamente con `run.sh`

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENTES (Streamlit)                    │
├──────────────────────┬──────────────────────────────────────┤
│  Cliente Principal   │     Dashboard Administrativo         │
│  (Chat & Feedback)   │     (Métricas & Estadísticas)        │
└──────────────┬───────┴──────────────────┬───────────────────┘
               │                          │
               └──────────────┬───────────┘
                              │
         ┌────────────────────▼────────────────────┐
         │     API FastAPI (Puerto 9000)           │
         │  Servidor RAG con Métricas Integradas   │
         └────────────┬───────────────────┬────────┘
                      │                   │
        ┌─────────────▼─┐    ┌───────────▼──────┐
        │    Ollama     │    │   FAISS Index    │
        │  Embeddings   │    │  + Q&A Cache     │
        │  + LLM        │    │  + Redis         │
        └───────────────┘    └──────────────────┘
                      │
         ┌────────────▼────────────┐
         │  Métricas & Logging     │
         │ (Prometheus + Custom)   │
         └─────────────────────────┘
```

### Archivos Clave

| Archivo | Función |
|---------|---------|
| `mcp_server_local.py` | 🎯 Servidor FastAPI con RAG + Métricas |
| `appclient/app_client.py` | 💬 Interfaz chat con autenticación |
| `appclient/app_admin.py` | 📊 Dashboard de métricas |
| `preprocess.py` | 🔄 Procesamiento inicial de documentos |
| `rag.py` | 🤖 Agente RAG con LangChain |
| `run.sh` | 🚀 Script de ejecución automatizado |

---

## 📊 Sistema de Métricas Detallado

### 1. Captura de Métricas Cuantitativas

**Ubicación**: `mcp_server_local.py` (líneas 70-80)

```python
# Metrics Prometheus
query_counter = Counter('queries_total', 'Total queries processed')
response_time = Histogram('response_time_seconds', 'Response time in seconds')
cache_hit_counter = Counter('cache_hits_total', 'Total cache hits')
error_counter = Counter('errors_total', 'Total errors')
cpu_usage = Gauge('cpu_usage_percent', 'Current CPU usage')
memory_usage = Gauge('memory_usage_percent', 'Current memory usage')
sentiment_score = Gauge('response_sentiment', 'Average sentiment')
hallucination_counter = Counter('hallucinations_total', 'Total hallucinations')
```

### 2. Captura de Métricas Cualitativas

**En endpoint `/ask`** (líneas 190-280):

```python
# Análisis de Sentimientos (NLTK)
sentiment = sia.polarity_scores(full_response)['compound']

# Detección de Alucinaciones
is_hallucinated = detect_hallucination(full_response, context)

# Categorización de Consultas
category = categorize_query(request.question)

# Tracking de Respuestas
qualitative_metrics["response_times"].append(response_time_val)
```

### 3. Endpoint de Feedback `/feedback`

**En líneas 290-310**, permite al usuario:

```python
{
    "question": "¿Cuál es el costo?",
    "response": "El costo es...",
    "satisfaction": 4,           # 1-5
    "clarity": 5,               # 1-5
    "completeness": 4,          # 1-5
    "error_type": "Incomplete",
    "comments": "Faltó info..."
}
```

### 4. Endpoint de Métricas `/metrics`

**En líneas 315-340**, retorna:

```json
{
  "quantitative": {
    "cpu_usage_percent": 25.5,
    "memory_usage_percent": 68.2,
    "queries_total": 42.0,
    "cache_hits_total": 18.0,
    "errors_total": 1.0,
    "hallucinations_total": 0.0
  },
  "qualitative": {
    "avg_satisfaction": 4.2,
    "avg_clarity": 4.5,
    "avg_completeness": 3.8,
    "hallucination_rate": 0.0,
    "avg_sentiment": 0.65,
    "query_categories": {
      "Costos": 15,
      "Contenidos": 12,
      "Admisión": 8,
      "Horarios": 4,
      "Políticas": 2,
      "Docentes": 1
    },
    "error_types": {
      "Timeout": 1
    }
  }
}
```

### 5. Dashboard Admin `/appclient/app_admin.py`

Visualización interactiva de:
- 📊 Gráficos de distribución de queries
- 📈 Tendencias de satisfacción temporal
- 🎯 Categorías de preguntas más frecuentes
- ❌ Tipos de errores
- 💾 Uso de recursos (CPU/Memoria)
- 📋 Tabla con últimos feedbacks

---

## 🔧 Configuración Personalizada

### Variables de Entorno

```bash
# En run.sh o terminal antes de ejecutar
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
```

### Ajustes del Modelo LLM

Editar en `mcp_server_local.py` línea 102:

```python
llm = OllamaLLM(
    model="promptnow/llama-3-typhoon-v1.5-8b-instruct-q4_k_m",
    temperature=0.2,      # Baja para precisión, alta para creatividad
    top_k=50,            # Tokens considerados
    top_p=0.95,          # Nucleus sampling
    num_ctx=8192         # Ventana de contexto
)
```

### Categorías de Consultas

Modificar en `mcp_server_local.py` línea 155:

```python
categories = {
    "Costos": ["costo", "precio", "matrícula", ...],
    "Contenidos": ["módulo", "curso", ...],
    # Agregar nuevas categorías según necesidad
}
```

---

## 📈 Historial de Cambios y Mejoras

### Fase 1: Fundamentos RAG (Inicial)
- ✅ Integración Ollama + FAISS
- ✅ Sistema de caché local
- ✅ Búsqueda semántica

### Fase 2: Mejoras de Precisión (v2.0)
- ✅ Semantic Chunking con LangChain
- ✅ Agentic RAG con herramientas
- ✅ Few-shot prompting dinámico
- ✅ Upgrade modelo: phi3:3.8b → llama-3-typhoon

### Fase 3: Experiencia de Usuario (v3.0)
- ✅ Autenticación de usuarios (login/registro)
- ✅ Interfaz Streamlit mejorada
- ✅ Feedback del usuario con Likert scale
- ✅ Tracking de tiempos de respuesta

### Fase 4: Sistema de Métricas (v4.0) ⭐ **ACTUAL**
- ✅ Métricas Prometheus cuantitativas
- ✅ Análisis de sentimientos (NLTK)
- ✅ Detección de alucinaciones
- ✅ Categorización automática de queries
- ✅ Dashboard administrativo completo
- ✅ Endpoint `/metrics` con agregaciones
- ✅ Endpoint `/feedback` para ratings
- ✅ Persistencia de historiales JSON
- ✅ Logging estructurado en `metrics.log`

### Mejoras Futuras (v5.0+)
- 🔜 GraphRAG para análisis relacional
- 🔜 Exportación de reportes PDF
- 🔜 Base de datos para métricas históricas
- 🔜 API de análisis predictivo
- 🔜 Integración con sistemas académicos

---

## 🎯 Flujo de Operación

### Para Usuarios (Cliente Principal)

```
1. Acceder a http://localhost:8501
   │
2. Crear cuenta o Loguearse
   │
3. Realizar pregunta
   │
4. Recibir respuesta + tiempo de procesamiento
   │
5. Calificar satisfacción/claridad/completitud (opcional)
   │
6. Ver histórico de conversaciones
```

### Para Administradores (Dashboard)

```
1. Acceder a http://localhost:8502
   │
2. Ver métricas cuantitativas en tiempo real
   │
3. Analizar distribución de preguntas
   │
4. Revisar sentimiento y satisfacción
   │
5. Identificar problemas (alucinaciones, errores)
   │
6. Exportar datos para análisis
```

### Para Investigadores (Datos Brutos)

```
1. Acceder endpoints /metrics y /feedback
   │
2. Descargar datos JSON
   │
3. Realizar análisis estadístico
   │
4. Generar reportes académicos
```

---

## 🛠️ Resolución de Problemas

### ❌ "Error: Ollama no está corriendo"
```bash
# En terminal separada
ollama serve

# O si está instalado como servicio
sudo systemctl start ollama
```

### ❌ "Error: Redis no disponible"
```bash
# En terminal separada
redis-server

# O si está instalado como servicio
sudo systemctl start redis-server
```

### ❌ "Puerto 8501/8502 ya en uso"
```bash
# Encontrar proceso
lsof -i :8501

# Matar proceso
kill -9 <PID>

# O cambiar puerto en run.sh
streamlit run appclient/app_client.py --server.port=8503
```

### ❌ "Métricas no se actualizan"
```bash
# Verificar que servidor está respondiendo
curl http://localhost:9000/health

# Ver logs del servidor
tail -f server.log

# Limpiar caché local
rm -f user_histories.json users.json
```

---

## 📚 Documentación Adicional

| Documento | Contenido |
|-----------|----------|
| [ArqAi.xml](ArqAi.xml) | Diagrama arquitectónico en Draw.io |
| [documentos/Preguntas_Frecuentes.txt](documentos/Preguntas_Frecuentes.txt) | Base de conocimiento original |
| [requirements.txt](requirements.txt) | Dependencias del proyecto |
| [metrics.log](metrics.log) | Registros detallados de operación |

---

## 📜 Justificación de Decisiones Técnicas

### ¿Por qué Ollama + Llama 3 Typhoon?

**Ollama**: Permite ejecutar LLMs localmente sin depender de APIs externas
- ✅ Control total de datos (privacidad para investigación académica)
- ✅ Costo operacional bajo
- ✅ Latencia reducida

**Llama 3 Typhoon**: Modelo especializado en precisión y seguimiento de instrucciones
- ✅ Mejor que phi3:3.8b en comprensión contextual
- ✅ Mejor que llama2 en calidad de respuestas
- ✅ Eficiente en recursos (Q4 quantization)

### ¿Por qué Prometheus para métricas?

- ✅ Estándar de facto en MLOps/DevOps
- ✅ Compatible con herramientas de análisis
- ✅ Histórico de datos para tendencias
- ✅ Alertas y notificaciones automáticas

### ¿Por qué Streamlit para UI?

- ✅ Desarrollo rápido sin frontend framework
- ✅ Interactivo y responsive
- ✅ Ideal para prototipos y MVP
- ✅ Manejo fácil de estado con sesiones

### ¿Por qué FAISS para búsqueda?

- ✅ Búsqueda vectorial eficiente en CPU
- ✅ Índices comprimidos y rápidos
- ✅ Escalable a millones de vectores
- ✅ Integración nativa con LangChain

---

## 1. Prerrequisitos

Asegúrate de tener lo siguiente instalado en tu sistema:

- **Python 3.12** o superior.
- **Ollama**: Asegúrate de que el servicio de Ollama esté en ejecución.
- **Modelos de Ollama**: Descarga los modelos necesarios.
  ```bash
  ollama pull promptnow/llama-3-typhoon-v1.5-8b-instruct-q4_k_m
  ollama pull nomic-embed-text
  ```
- **Redis**: Caché distribuido para operaciones óptimas.

## 2. Configuración del Entorno

1. **Crear Entorno Virtual**:
   ```bash
   python3 -m venv venmcp
   ```

2. **Activar Entorno Virtual**:
   - En **Linux/macOS**:
     ```bash
     source venmcp/bin/activate
     ```
   - En **Windows**:
     ```bash
     venmcp\Scripts\activate
     ```

3. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

## 3. Ejecución Simplificada (Recomendado)

```bash
chmod +x run.sh
./run.sh                # Cliente solo
./run.sh --admin       # Con dashboard de métricas
```

## 4. Ejecución Manual

### Generar Archivos Iniciales

```bash
python preprocess.py
```

### Iniciar Servidor

```bash
python mcp_server_local.py
```

### Iniciar Cliente

```bash
streamlit run appclient/app_client.py
```

### Iniciar Dashboard

```bash
streamlit run appclient/app_admin.py --server.port=8502
```

## 5. Probar la API

```bash
curl -X POST "http://localhost:9000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el costo de la maestría?"}'
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/MejoraNombre`)
3. Commit cambios (`git commit -am 'Agregar mejora'`)
4. Push a rama (`git push origin feature/MejoraNombre`)
5. Abrir Pull Request

---

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para detalles.

---

## 📞 Contacto y Soporte

Para preguntas sobre:
- **Implementación técnica**: Revisar [mcp_server_local.py](mcp_server_local.py)
- **Métricas de investigación**: Consultar docentes asesores
- **Errores del sistema**: Revisar [metrics.log](metrics.log)

---

## 🎓 Cita Académica

Si utilizas este proyecto en investigación, por favor cita:

```bibtex
@software{soebot2026,
  title={SoeBOT: Sistema RAG Inteligente con Métricas de Investigación},
  author={[Tu Nombre]},
  year={2026},
  institution={[Tu Institución]},
  url={https://github.com/[usuario]/soebot}
}
```

---

**Última actualización**: Enero 20, 2026  
**Versión**: 4.0 - Sistema de Métricas Completo  
**Estado**: ✅ Producción - Validado y Operacional
