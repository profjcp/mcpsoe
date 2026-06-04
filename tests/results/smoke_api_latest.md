# Smoke API Results

- Timestamp: 2026-06-03T20:13:33-04:00
- Base URL: http://localhost:9000

## Health
```json
{"status":"healthy","timestamp":"2026-06-03T20:13:33.822920"}

```

## Ask Guidance
```json
Puedo ayudarte mejor si escribes una pregunta concreta dentro del contexto de SoeBOT.

Áreas que manejo:
1. Atención al cliente: inscripciones, certificados, pagos, Moodle y trámites.
2. Académica: programas, módulos, horarios y docentes.
3. Investigación: tutor, monografía, defensa y curso de actualización.

Ejemplos de preguntas útiles:
- ¿Cómo puedo subir una tarea a Moodle?
- ¿Cuáles son los horarios de Ciberseguridad?
- ¿Cómo puedo obtener mi tutor?
- ¿Cuáles son los documentos de inscripción?

```

## Ask FAQ
```json
Respuesta (AtencionCliente):
Pregunta: ¿Cuáles son los documentos de Inscripción?
Respuesta: - 2 fotocopia Legalizada del Título en Provisión Nacional
- 1 fotocopia simple de Cédula de Identidad
- 3 fotografía 3x3 fondo rojo, traje formal
- Formulario de solicitud de Inscripción (según formato de la UAGRM School)
- Hoja de vida (según formato de la UAGRM School of Engineering).

```

## Ask Cache Repeat
```json
Respuesta (AtencionCliente):
Pregunta: ¿Cuáles son los documentos de Inscripción?
Respuesta: - 2 fotocopia Legalizada del Título en Provisión Nacional
- 1 fotocopia simple de Cédula de Identidad
- 3 fotografía 3x3 fondo rojo, traje formal
- Formulario de solicitud de Inscripción (según formato de la UAGRM School)
- Hoja de vida (según formato de la UAGRM School of Engineering).

```

## Ask RAG DOC
```json
No tengo suficiente información para responder esta pregunta.

```

## Feedback OK
```json
{"message":"Feedback guardado","status":"success"}

```

## Metrics
```json
{"quantitative":{"cpu_usage_percent":0.0,"memory_usage_percent":55.2,"queries_total":164,"cache_hits_total":5,"errors_total":25,"hallucinations_total":0},"qualitative":{"avg_satisfaction":2.71,"avg_clarity":2.59,"avg_completeness":2.63,"hallucination_rate":0.0,"avg_sentiment":0.0,"avg_response_time":39.03,"query_categories":{"['Otro']":64,"['Academica']":38,"['Academica', 'Investigacion']":1,"['AtencionCliente', 'Academica']":11,"['AtencionCliente']":29,"['Investigacion']":17,"['AtencionCliente', 'Investigacion']":5},"error_types":{"Contexto insuficiente":13,"Interpretación errónea":1,"Alucinacion":2,"Formato incorrecto":1,"Interpretacion erronea":8},"total_queries_tracked":164},"per_user":{"verificacion_metricas":{"queries_total":1,"faq_hits_total":0,"cache_hits_total":0,"guidance_total":1,"rag_total":0,"history_import_total":0,"errors_total":0,"hallucinations_total":0,"avg_response_time":0.0,"avg_satisfaction":5.0,"avg_clarity":5.0,"avg_completeness":5.0,"query_categories":{"Otro":1},"error_types":{}},"jcpeinado":{"queries_total":67,"faq_hits_total":3,"cache_hits_total":2,"guidance_total":4,"rag_total":1,"history_import_total":57,"errors_total":1,"hallucinations_total":0,"avg_r
```

## Ask Invalid Payload (expect 422)
- HTTP status: 422
```json
{"detail":[{"type":"missing","loc":["body","question"],"msg":"Field required","input":{"user_id":"smoke_invalid"}}]}
```

