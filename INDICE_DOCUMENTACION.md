# 📚 Índice de Documentación - SoeBOT v4.0

## 🎯 Empezar Aquí

Si es tu **primera vez** visitando el proyecto:

1. Lee [README.md](README.md) - Visión general y inicio rápido
2. Ejecuta `./run.sh --admin` para ver el sistema en acción
3. Accede a http://localhost:8501 (cliente) y http://localhost:8502 (admin)

---

## 📄 Documentos Principales

### 1. [README.md](README.md) - Guía Completa (629 líneas)

**Contenido**:
- 📋 Descripción general del proyecto
- 🎯 ¿Por qué se agregaron las métricas?
- 💡 16+ Beneficios documentados
- 🚀 Inicio rápido en 3 pasos
- 📦 Requisitos y dependencias
- 🏗️ Arquitectura del sistema
- 📊 Sistema de métricas detallado
- 🔧 Configuración personalizada
- 📈 Historial de cambios (4 fases)
- 🎯 Flujos de operación
- 🛠️ Troubleshooting
- 📜 Justificación técnica

**Para quién**:
- 👤 Usuarios nuevos
- 🎓 Investigadores
- 🏢 Administradores
- 👨‍💻 Desarrolladores

---

### 2. [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md) - Detalles Técnicos (400+ líneas)

**Contenido**:
- 📊 15 Métricas implementadas (desglose completo)
- 🔌 Endpoints nuevos/modificados con ejemplos JSON
- 💻 Cambios en clientes (auth, feedback, admin dashboard)
- 📁 Nuevos archivos de persistencia
- 🔍 Algoritmos de detección (alucinaciones, sentimiento)
- 🏷️ Categorización de consultas
- 🔄 Flujos de captura de datos
- 📊 Agregación de métricas
- 🎓 Beneficios para investigación
- 🔮 Mejoras futuras
- ✅ Checklist de implementación

**Para quién**:
- 👨‍💻 Desarrolladores
- 🔬 Investigadores técnicos
- 🏗️ Arquitectos del sistema
- 📊 Analistas de datos

---

## 🗂️ Estructura de Archivos Clave

```
mcpsoe/
├── README.md                 ← ⭐ EMPIEZA AQUÍ
├── CAMBIOS_METRICAS.md       ← Detalles técnicos
├── INDICE_DOCUMENTACION.md   ← Estás aquí
│
├── mcp_server_local.py       🤖 Servidor RAG + Métricas (354 líneas)
│   ├─ Endpoints: /ask, /feedback, /metrics, /health
│   ├─ Métricas Prometheus
│   ├─ Análisis de sentimientos y alucinaciones
│   └─ Categorización de consultas
│
├── appclient/
│   ├─ app_client.py         💬 Cliente chat (196 líneas)
│   │  ├─ Login/registro
│   │  ├─ Chat con feedback
│   │  └─ Tracking de tiempos
│   │
│   └─ app_admin.py          📊 Dashboard admin (250+ líneas)
│      ├─ Métricas en tiempo real
│      ├─ Gráficos y visualizaciones
│      └─ Tabla de feedbacks
│
├── preprocess.py            🔄 Procesamiento inicial
├── rag.py                   🤖 Agente RAG
├── requirements.txt         📦 Dependencias (21 librerías)
├── run.sh                   🚀 Script de ejecución
│
├── documentos/
│   ├─ Preguntas_Frecuentes.txt  📚 Base de conocimiento
│   └─ Esquema/ArqAi.png         🏗️ Diagrama arquitectónico
│
├── faiss_index.bin          📍 Índice FAISS (chunks)
├── qa_faiss_index.bin       📍 Índice Q&A (caché)
├── chunks.pkl               💾 Chunks procesados
├── qa_cache.pkl             💾 Respuestas cacheadas
│
├── users.json               👤 Base de usuarios
├── user_histories.json      💬 Historiales de chats
├── metrics.log              📋 Logs del servidor
│
└── venmcp/                  🐍 Entorno virtual Python 3.12
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
| ¿Cómo inicio? | README.md | Inicio Rápido |
| ¿Qué son las métricas? | README.md | ¿Por Qué Métricas? |
| ¿Cuáles son los beneficios? | README.md | Beneficios de Métricas |
| ¿Cómo funciona? | README.md | Arquitectura |
| ¿Qué métricas se capturan? | CAMBIOS_METRICAS.md | Métricas Implementadas |
| ¿Cómo se usan los endpoints? | CAMBIOS_METRICAS.md | Endpoints |
| ¿Hay problemas? | README.md | Troubleshooting |
| ¿Qué mejorar en futuro? | CAMBIOS_METRICAS.md | Mejoras Futuras |

---

## 📞 Contacto y Soporte

Para preguntas específicas:

| Pregunta | Contactar |
|----------|-----------|
| Implementación técnica | Ver [mcp_server_local.py](mcp_server_local.py) |
| Métricas de investigación | Consultar asesores de tesis |
| Errores del sistema | Revisar [metrics.log](metrics.log) |
| Documentación faltante | Revisar [CAMBIOS_METRICAS.md](CAMBIOS_METRICAS.md) |

---

## ✨ Hoja de Ruta de Documentación

### ✅ Completado (v4.0)
- [x] Documentación completa del proyecto
- [x] Explicación de métricas
- [x] Beneficios documentados
- [x] Ejemplos de código
- [x] Troubleshooting
- [x] Índice de navegación

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
