---
applyTo: "mcp_server_local.py,appclient/app_admin.py,experiments/**/*.py,experiments/**/*.md,CAMBIOS_METRICAS.md"
---

# Métricas y tesis doctoral

## Objetivo
Preservar la trazabilidad de interacciones y la validez de métricas globales y por usuario para el análisis doctoral del proyecto SoeBOT.

## Reglas clave
- No redefinir métricas existentes sin solicitud explícita.
- Mantener compatibilidad con datos `legacy` y con los archivos persistentes `feedback.jsonl`, `interaction_logs.jsonl`, `user_histories.json` y `users.json`.
- Al modificar `/metrics` o el dashboard admin, priorizar comparabilidad histórica y claridad metodológica.
- Evitar cambios que oculten usuarios con histórico importado o registros backfilled.
- Si se añade una visualización, acompañarla con una interpretación breve y útil para tesis.
- Conservar exportes y filtros por usuario, categoría y periodo cuando ya existan.

## Validación sugerida
- Verificar que `/metrics` siga respondiendo correctamente.
- Confirmar que el panel admin muestre análisis global y por usuario.
- Asegurar que un reinicio del servicio no pierda trazabilidad ni conteos históricos.
