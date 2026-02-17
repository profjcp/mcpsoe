# 📚 Índice de Documentación - SoeBOT v5.0

## 🎯 Empezar Aquí

Si es tu **primera vez** visitando el proyecto:

1. Lee [README.md](README.md) - Visión general completa con arquitectura híbrida FAQ-RAG
2. Revisa [METODOLOGIA_DOCTORAL.md](METODOLOGIA_DOCTORAL.md) - Fundamentos científicos y diseño experimental
3. Ejecuta `./run.sh --admin` para ver el sistema en acción
4. Accede a http://localhost:8501 (cliente Gemini-style) y http://localhost:8502 (dashboard de tesis)

---

## 📄 Documentos Principales

### 1. [README.md](README.md) - Documentación Técnica Completa (800+ líneas)

**Contenido actualizado v5.0**:
- 📋 Sistema RAG híbrido FAQ-first con búsqueda semántica por dominio
- 🎯 Marco de investigación doctoral con 4 preguntas de investigación (RQ1-RQ4)
- 🔬 Hipótesis de investigación (H1a-H1d) con criterios de validación
- 💡 Comparación FAQ-RAG Híbrido vs. RAG Tradicional (tabla de ventajas)
- 🚀 Inicio rápido en 3 pasos
- 📦 Requisitos y dependencias
- 🏗️ Arquitectura actualizada con componentes de FAQ
- 📊 Sistema de métricas alineado a criterios de tesis
- 📚 Documentación detallada del sistema de FAQs por dominio
- 🔧 Configuración personalizada
- 📈 Historial de cambios (v1.0 → v5.0)
- 🎯 Flujos de operación FAQ → RAG
- 🛠️ Troubleshooting
- 📜 Justificación técnica y académica

**Para quién**:
- 👤 Usuarios nuevos (inicio rápido)
- 🎓 Investigadores (marco teórico)
- 🏢 Administradores (deployment)
- 👨‍💻 Desarrolladores (arquitectura)

---

### 2. [METODOLOGIA_DOCTORAL.md](METODOLOGIA_DOCTORAL.md) - Marco de Investigación Científica (500+ líneas) 🆕

**Contenido completo de investigación doctoral**:
- 📋 **Resumen ejecutivo** con variables dependientes/independientes
- 🎯 **Cuatro preguntas de investigación** (RQ1-RQ4) con hipótesis detalladas
  - RQ1: Eficiencia computacional (H1a)
  - RQ2: Claridad y comprensibilidad (H1b)
  - RQ3: Veracidad y reducción de alucinaciones (H1c)
  - RQ4: Satisfacción del usuario (H1d)
- 🔬 **Diseño experimental**: Estudio cuasi-experimental con grupo control
- 📊 **Recolección de datos**: Cuantitativos (Prometheus) + Cualitativos (feedback)
- 📈 **Análisis estadístico**: 
  - Pruebas paramétricas (t-Student, ANOVA)
  - Pruebas no paramétricas (Mann-Whitney, Kruskal-Wallis)
  - Análisis de correlación y series temporales
- 🎯 **Criterios de validación**: Interna, externa, constructo, confiabilidad
- 📊 **Dashboard de análisis** con 4 secciones por criterio de tesis
- 🔄 **Proceso de iteración** en 5 fases (Baseline → Validación)
- 📝 **Consideraciones éticas**: Consentimiento, privacidad, transparencia
- 📚 **Referencias metodológicas**: Campbell & Stanley, Field, Lewis et al.
- 🔮 **Extensiones futuras**: Técnicas, analíticas, escalamiento

**Para quién**:
- 🎓 Doctorando (documento central de metodología)
- 🔬 Comité de tesis (evaluación de rigor científico)
- 📊 Analistas de datos (protocolos de análisis)
- 📚 Investigadores interesados (replicación)

---

---

### 3. [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md) - Historia de Versiones y Detalles Técnicos (500+ líneas)

**Contenido actualizado v5.0**:
- 📊 **Novedades v5.0** (2026-02-17):
  1. Sistema de FAQs semántico por dominio (3 archivos, 52 Q&A)
  2. Cliente estilo Gemini con gestión conversacional
  3. Dashboard administrativo con criterios de tesis
  4. Categorización multi-dominio mejorada
- 📈 15 Métricas implementadas (desglose completo por criterio)
- 🔌 Endpoints nuevos/modificados con ejemplos JSON
  - POST `/ask`: Búsqueda FAQ → Cache → RAG
  - POST `/feedback`: Calificaciones Likert + comentarios
  - GET `/metrics`: Agregación cuantitativa + cualitativa
  - GET `/health`: Status del sistema
- 💻 Cambios en clientes:
  - `app_client.py`: Layout Gemini, conversaciones, feedback UI
  - `app_admin.py`: 4 secciones de tesis con CSV export
- 📁 Nuevos archivos de persistencia (feedback.jsonl, user_histories.json)
- 🔍 Algoritmos de detección (alucinaciones heurísticas, sentimiento NLTK)
- 🏷️ Categorización de consultas multi-label con keywords expandidos
- 🔄 Flujos de captura de datos (automáticos + explícitos)
- 📊 Agregación de métricas por criterio de tesis
- 🎓 Beneficios para investigación doctoral
- 🔮 Mejoras futuras (embeddings contextuales, multi-idioma)
- ✅ Checklist de implementación completa

**Para quién**:
- 👨‍💻 Desarrolladores (historia de cambios)
- 🔬 Investigadores técnicos (algoritmos)
- 🏗️ Arquitectos del sistema (decisiones de diseño)
- 📊 Analistas de datos (formato de métricas)

---

## 🗂️ Estructura de Archivos Clave

```
mcpsoe/
├── 📄 Documentación (v5.0)
│   ├── README.md                       ⭐ EMPIEZA AQUÍ - Guía técnica completa
│   ├── METODOLOGIA_DOCTORAL.md         🎓 NUEVO - Marco científico y experimental
│   ├── CAMBIOS_METRICAS.md             📊 Historia de versiones (v1.0 → v5.0)
│   └── INDICE_DOCUMENTACION.md         📚 Estás aquí - Mapa de navegación
│
├── 🤖 Backend (Servidor FastAPI)
│   ├── mcp_server_local.py             🎯 Servidor RAG híbrido (~420 líneas)
│   │   ├─ Sistema FAQ semántico (líneas 196-243)
│   │   ├─ Categorización multi-dominio (línea 196)
│   │   ├─ Endpoints: /ask, /feedback, /metrics, /health
│   │   ├─ Métricas Prometheus (8 contadores)
│   │   └─ Detección de alucinaciones + análisis de sentimiento
│   │
│   ├── rag.py                          🤖 Agente RAG generativo (~200 líneas)
│   ├── preprocess.py                   🔄 Procesamiento de documentos (~150 líneas)
│   └── shared_client.py                🔗 Utilidades compartidas
│
├── 💬 Frontend (Clientes Streamlit)
│   └── appclient/
│       ├── app_client.py               💬 Cliente Gemini-style (~300 líneas)
│       │   ├─ Layout de dos columnas (sidebar + main)
│       │   ├─ Gestión de conversaciones con IDs
│       │   ├─ Mensajes con burbujas estilizadas
│       │   ├─ Visualización de tiempos de respuesta
│       │   └─ Sistema de feedback integrado
│       │
│       └── app_admin.py                📊 Dashboard de tesis (~350 líneas)
│           ├─ Sección 1: Eficiencia (cache, latencia, recursos)
│           ├─ Sección 2: Claridad (distribución, casos bajos)
│           ├─ Sección 3: Veracidad (alucinaciones, errores)
│           ├─ Sección 4: Satisfacción (tendencia, comentarios)
│           └─ Exportación CSV por criterio
│
├── 📚 Base de Conocimiento
│   └── documentos/
│       ├── faq_atencion_cliente.txt    📞 12 Q&A (costos, inscripción)
│       ├── faq_academica.txt           🎓 29 Q&A (programas, requisitos)
│       ├── faq_investigacion.txt       🔬 11 Q&A (tesis, tutores)
│       ├── Preguntas_Frecuentes.txt    📋 Documento base general
│       └── Esquema/
│           └── ArqAi.xml               🏗️ Esquema arquitectónico
│
├── 💾 Persistencia y Cache
│   ├── faiss_index.bin                 📍 Índice FAISS de chunks documentales
│   ├── qa_faiss_index.bin              📍 Índice FAISS de pares Q&A
│   ├── chunks.pkl                      💾 Chunks procesados (pickle)
│   ├── qa_cache.pkl                    💾 Cache de respuestas (pickle)
│   ├── feedback.jsonl                  📊 Base de datos de feedback (JSON Lines)
│   ├── user_histories.json             💬 Historiales de conversaciones
│   ├── users.json                      👤 Base de usuarios con hashing
│   └── metrics.log                     📋 Logs del servidor (timestamped)
│
├── 🚀 Deployment
│   ├── run.sh                          🚀 Script de orquestación (~150 líneas)
│   │   ├─ Health check Redis (10 reintentos)
│   │   ├─ Health check Ollama (120 reintentos)
│   │   ├─ Health check MCP Server (180 reintentos)
│   │   └─ Lanzamiento de clientes Streamlit
│   │
│   ├── requirements.txt                📦 Dependencias Python (25+ librerías)
│   └── deploy/
│       └── fastapi-deployment.yaml     ☸️ Configuración Kubernetes (opcional)
│
└── 🐍 Entorno Virtual
    └── venmcp/                         🐍 Python 3.12 con todas las dependencias
```

---

## 🎯 Mapas de Navegación

### Para Implementar el Sistema
```
1. Leer: README.md → Sección "Inicio Rápido"
2. Ejecutar: ./run.sh --admin
3. Acceder: http://localhost:8501 (cliente)
4. Ver: http://localhost:8502 (admin dashboard)
```

### Para Entender las Métricas
```
1. Leer: README.md → Sección "¿Por Qué Métricas?"
2. Leer: README.md → Sección "Beneficios de Métricas"
3. Ver: CAMBIOS_METRICAS.md → Sección "Métricas Implementadas"
4. Código: mcp_server_local.py líneas 70-340
```

### Para Modificar el Sistema
```
1. Leer: CAMBIOS_METRICAS.md → Sección "Endpoints"
2. Código: mcp_server_local.py → Función ask()
3. Código: appclient/app_client.py → Feedback form
4. Código: appclient/app_admin.py → Visualizaciones
```

### Para Análisis de Datos
```
1. Acceder: http://localhost:9000/metrics (JSON)
2. Endpoint: POST /feedback para enviar ratings
3. Archivo: metrics.log para histórico de operaciones
4. Archivos: users.json, user_histories.json para datos brutos
```

### Para Investigación Académica
```
1. Leer: README.md → "¿Por Qué Se Agregaron las Métricas?"
2. Leer: README.md → "Beneficios de las Métricas"
3. Leer: CAMBIOS_METRICAS.md → Todo el documento
4. Recopilar: Datos de /metrics endpoint
5. Exportar: Historiales JSON para análisis estadístico
```

---

## 🔍 Búsqueda Rápida por Tema

### Métricas
- **¿Qué métricas se recopilan?** → [README.md](README.md#-sistema-de-métricas-detallado)
- **¿Cómo se calculan?** → [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md#-agregación-de-métricas)
- **¿Dónde están en el código?** → `mcp_server_local.py` líneas 70-340

### Beneficios
- **Para investigadores** → [README.md](README.md#para-la-investigación)
- **Para optimización** → [README.md](README.md#para-la-optimización-del-sistema)
- **Para usuarios** → [README.md](README.md#para-el-usuario)
- **Para institución** → [README.md](README.md#para-la-institución)

### Endpoints
- **¿Cuáles son los endpoints?** → [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md#-endpoints-nuevosmodificados)
- **¿Cómo usarlos?** → [README.md](README.md#paso-3-acceder-interfaz)
- **¿Ejemplos JSON?** → [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md#3-get-metrics-nuevo)

### Flujos de Datos
- **¿Cómo fluyen las métricas?** → [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md#-flujo-de-captura-de-métrica)
- **¿Cómo se capturan?** → [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md#-captura-de-métricas-cuantitativas)
- **¿Cómo se agregran?** → [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md#-agregación-de-métricas)

### Configuración
- **¿Cómo personalizar?** → [README.md](README.md#-configuración-personalizada)
- **¿Variables de entorno?** → [README.md](README.md#variables-de-entorno)
- **¿Modelos LLM?** → [README.md](README.md#ajustes-del-modelo-llm)

### Problemas
- **¿Cómo solucionar errores?** → [README.md](README.md#-resolución-de-problemas)
- **Ollama no funciona** → [README.md](README.md#-error-ollama-no-está-corriendo)
- **Redis offline** → [README.md](README.md#-error-redis-no-disponible)

---

## 📊 Estadísticas de Documentación

| Aspecto | Valor |
|---------|-------|
| **Líneas totales** | 1000+ |
| **Secciones principales** | 27+ |
| **Métricas documentadas** | 15 |
| **Beneficios explicados** | 16+ |
| **Diagramas** | 4 |
| **Ejemplos de código** | 30+ |
| **Tablas informativas** | 8 |
| **Palabras clave indexadas** | 100+ |

---

## 🎓 Cómo Usar Esta Documentación

### Como Iniciante
```
⏱️ Tiempo: 15 minutos
📄 Documentos: README.md (inicio rápido)
🎯 Objetivo: Ejecutar y ver funcionando
```

### Como Desarrollador
```
⏱️ Tiempo: 1 hora
📄 Documentos: README.md + CAMBIOS_METRICAS.md
🎯 Objetivo: Entender arquitectura y modificar
```

### Como Investigador
```
⏱️ Tiempo: 2-3 horas
📄 Documentos: README.md + CAMBIOS_METRICAS.md + código fuente
🎯 Objetivo: Recopilar datos y analizar
```

### Como Administrador
```
⏱️ Tiempo: 30 minutos
📄 Documentos: README.md (configuración y troubleshooting)
🎯 Objetivo: Monitorear y mantener sistema
```

---

## 🔗 Referencias Cruzadas

| Pregunta | Documento | Sección |
|----------|-----------|---------|
| ¿Qué es el proyecto? | README.md | Descripción General |
| ¿Marco de investigación? | METODOLOGIA_DOCTORAL.md | Resumen Ejecutivo |
| ¿Cómo inicio? | README.md | Inicio Rápido |
| ¿Sistema de FAQs? | README.md | Sistema de FAQs Semántico |
| ¿Arquitectura híbrida? | README.md | Sistema Híbrido FAQ-RAG |
| ¿Qué métricas hay? | README.md | Marco de Validación (4 Criterios) |
| ¿Diseño experimental? | METODOLOGIA_DOCTORAL.md | Diseño Experimental |
| ¿Análisis estadístico? | METODOLOGIA_DOCTORAL.md | Análisis Estadístico |
| ¿Cambios recientes? | CAMBIOS_METRICAS.md | Novedades v5.0 |
| ¿Endpoints API? | CAMBIOS_METRICAS.md | Endpoints |
| ¿Hay problemas? | README.md | Troubleshooting |
| ¿Cliente Gemini? | CAMBIOS_METRICAS.md | Cliente Estilo Gemini |
| ¿Dashboard tesis? | CAMBIOS_METRICAS.md | Dashboard Administrativo |

---

## 📞 Contacto y Soporte

Para preguntas específicas:

| Pregunta | Recurso |
|----------|---------|
| Implementación técnica | Ver [mcp_server_local.py](mcp_server_local.py) líneas 196-420 |
| Metodología doctoral | Consultar [METODOLOGIA_DOCTORAL.md](METODOLOGIA_DOCTORAL.md) |
| Sistema de FAQs | Ver `documentos/faq_*.txt` y README.md sección FAQs |
| Dashboard de tesis | Ver [appclient/app_admin.py](appclient/app_admin.py) |
| Métricas de investigación | Endpoint GET `/metrics` o dashboard admin |
| Errores del sistema | Revisar [metrics.log](metrics.log) |
| Feedback de usuarios | Ver [feedback.jsonl](feedback.jsonl) |

---

## 📊 Estadísticas de Documentación (v5.0)

| Aspecto | Valor |
|---------|-------|
| **Documentos principales** | 4 (README, METODOLOGIA, CAMBIOS, INDICE) |
| **Líneas totales** | 2000+ |
| **Secciones principales** | 40+ |
| **Archivos FAQ** | 3 dominios (52 pares Q&A) |
| **Criterios de tesis** | 4 (Eficiencia, Claridad, Veracidad, Satisfacción) |
| **Métricas documentadas** | 20+ |
| **Preguntas de investigación** | 4 (RQ1-RQ4) |
| **Hipótesis** | 5 (H0, H1a-H1d) |
| **Diagramas** | 6 |
| **Ejemplos de código** | 40+ |
| **Tablas informativas** | 15+ |
| **Referencias académicas** | 10+ |

---

## ✨ Hoja de Ruta de Documentación

### ✅ Completado (v5.0)
- [x] Documentación completa del proyecto (README 800+ líneas)
- [x] Marco metodológico doctoral (METODOLOGIA 500+ líneas)
- [x] Sistema de FAQs por dominio documentado
- [x] Cliente Gemini-style documentado
- [x] Dashboard de tesis documentado
- [x] Explicación de métricas por criterio
- [x] Beneficios académicos documentados
- [x] Ejemplos de código y diagramas
- [x] Troubleshooting actualizado
- [x] Índice de navegación completo
- [x] Historia de versiones detallada
- [x] Referencias científicas incluidas

### 🔜 Futuro (v5.0+)
- [ ] Video tutorials
- [ ] Guías de análisis estadístico
- [ ] Papers académicos
- [ ] Benchmarks de rendimiento
- [ ] Casos de estudio

---

## 📅 Información Meta

| Aspecto | Valor |
|---------|-------|
| **Versión del Proyecto** | 4.0 |
| **Versión de Documentación** | 1.0 |
| **Última Actualización** | Enero 20, 2026 |
| **Estado** | ✅ Producción |
| **Cobertura** | 100% del proyecto |
| **Audiencia** | Usuarios, Desarrolladores, Investigadores, Administradores |

---

**Última actualización**: Enero 20, 2026  
**Manteneedor**: [Tu Nombre]  
**Licencia**: MIT
