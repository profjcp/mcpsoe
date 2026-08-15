# Reporte de Niveles de Respuesta (Funcion RAG)

**Fecha:** 2026-08-09T12:23:46.884704

**Total interacciones:** 6


## Distribucion de Clasificacion

| Clasificacion | N | % |
|---------------|---|----|
| posible_alucinacion | 4 | 66.7% |
| correcta | 2 | 33.3% |

## Niveles por Area

| Area | N | Correcta | Contexto insuf. | Posible aluc. | Timeout |
|------|---|----------|-----------------|---------------|---------|
| Academico | 1 | 1 | 0 | 0 | 0 |
| Administracion | 1 | 0 | 0 | 1 | 0 |
| AtencionCliente | 1 | 0 | 0 | 1 | 0 |
| Direccion | 1 | 0 | 0 | 1 | 0 |
| Investigacion | 1 | 0 | 0 | 1 | 0 |
| Marketing | 1 | 1 | 0 | 0 | 0 |

## Casos con Posible Alucinacion

- **cliente_01** (AtencionCliente): ¿Cómo puedo tramitar las certificaciones intermedias?...
  - Clasificacion: posible_alucinacion
  - Respuesta (primeros 150): Pregunta: ¿Cómo puedo tramitar las certificaciones intermedias?
Respuesta: Debe cumplir con los siguientes requisitos
1. Es requisito fundamental habe...
- **invest_01** (Investigacion): ¿Cómo puedo obtener mi tutor?...
  - Clasificacion: posible_alucinacion
  - Respuesta (primeros 150): Pregunta: ¿Cómo puedo obtener mi tutor?
Respuesta: Debe mandar un correo a: investigacion@soe.uagrm.edu.bo para que nuestra Coordinadora de Investigac...
- **admin_01** (Administracion): ¿Cuáles son los documentos de inscripción requeridos?...
  - Clasificacion: posible_alucinacion
  - Respuesta (primeros 150): Pregunta: ¿Cuáles son los documentos de Inscripción?
Respuesta: - 2 fotocopia Legalizada del Título en Provisión Nacional
- 1 fotocopia simple de Cédu...
- **direccion_01** (Direccion): ¿Cuál es el proceso para obtener la certificación intermedia...
  - Clasificacion: posible_alucinacion
  - Respuesta (primeros 150): Pregunta: ¿Cuánto tiempo tarda el proceso de certificación intermedia?
Respuesta: El tiempo del proceso puede variar según la revisión de documentos y...