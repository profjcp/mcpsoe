---
applyTo: "mcp_server_local.py,rag.py,shared_client.py,mcp_lib/**/*.py"
---

# Backend SoeBOT

## Objetivo
Mantener estable la lógica de preguntas, FAQs, métricas y persistencia.

## Reglas específicas
- Antes de activar guidance, intentar responder por FAQ si la pregunta es concreta.
- Al tocar categorización, evitar mezclar dominios entre atención, académica e investigación.
- Preservar el registro por usuario para análisis de tesis.
- Si se propone una mejora, debe ser compatible con los logs históricos y registros legacy.
- No eliminar campos usados por el dashboard admin.

## Buenas prácticas
- Preferir fixes de causa raíz.
- Mantener respuestas concisas y útiles para estudiantes.
- Evitar regresiones en consultas tipo:
  - `¿Cómo puedo subir una tarea a Moodle?`
  - `¿Cómo puedo obtener mi tutor?`
