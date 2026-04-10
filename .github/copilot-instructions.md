# Instrucciones generales del proyecto SoeBOT

## Contexto del sistema
- Este repositorio implementa un asistente académico para SOE/UAGRM.
- El backend principal está en `mcp_server_local.py`.
- Los clientes están en `appclient/app_client.py` y `appclient/app_admin.py`.
- Las FAQs están en `documentos/faq_atencion_cliente.txt`, `documentos/faq_academica.txt` y `documentos/faq_investigacion.txt`.

## Reglas de trabajo
- Mantener textos y respuestas visibles al usuario en español claro y formal.
- No romper compatibilidad con los endpoints `/ask`, `/feedback`, `/metrics` y `/health`.
- No inventar nuevas métricas ni cambiar su significado sin solicitud explícita.
- Priorizar cambios pequeños, claros y consistentes con la estructura actual.
- Si se modifica la lógica FAQ, preservar la separación por dominio: Académica, Atención al Cliente e Investigación.

## Persistencia y datos
- Respetar los archivos persistentes usados por el sistema:
  - `feedback.jsonl`
  - `interaction_logs.jsonl`
  - `user_histories.json`
  - `users.json`
- No asumir que los datos en memoria son la única fuente de verdad.

## Estilo esperado
- Explicar brevemente el motivo técnico de un cambio.
- Reutilizar funciones existentes antes de duplicar lógica.
- Mantener nombres descriptivos y coherentes con el código actual.
