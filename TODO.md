# TODO - Auto-reinicio del servidor MCP

## Pasos a completar

- [x] Diagnóstico del problema (OOM kill del servidor MCP)
- [x] Crear script watchdog `restart_mcp.sh` que monitoree el puerto 9000 y reinicie el MCP server automáticamente
- [x] Modificar `run.sh` para delegar el arranque del MCP al watchdog (auto-reinicio)
- [x] Probar el reinicio automático (matar el proceso y verificar que se levante solo)
