# Plan Experimental T1 - Baterías Automáticas SoeBOT

## 1) Objetivo
Validar automáticamente el comportamiento del sistema SoeBOT para la fase T1, simulando múltiples usuarios y preguntas con variaciones lingüísticas, sin intervención humana durante la ejecución.

## 2) Alcance de validez (sin intervención humana)
Las baterías automáticas son válidas para:
- Eficiencia: latencia, p95, throughput
- Estabilidad: tasa de error, timeouts, respuesta bajo concurrencia
- Enrutamiento funcional: cobertura por dominio (Atención, Académica, Investigación)
- Exactitud aproximada FAQ: similitud automática contra respuesta esperada

Limitación metodológica:
- Claridad percibida y satisfacción humana deben complementarse con grupo focal real.

## 3) Hipótesis operativas para T1
- H1: p95 de latencia < 8 segundos con hasta 10 usuarios concurrentes.
- H2: tasa de error HTTP < 3% durante carga escalonada.
- H3: al menos 70% de casos FAQ alcanzan similitud >= umbral automático.
- H4: el sistema procesa consultas multiusuario sin caída de servicio.

## 4) Diseño experimental
### 4.1 Variables
- Independientes:
  - Concurrencia: 1, 5, 10 usuarios
  - Volumen: número total de consultas
  - Tipo de variación de pregunta: original, sin acentos, typo leve, reformulación
- Dependientes:
  - `latency_ms`, `http_status`, `success_rate`, `faq_hit_ratio`, `similarity_ratio`

### 4.2 Dataset de pruebas
- Fuente: FAQs en `documentos/faq_*.txt`
- Se generan preguntas derivadas automáticamente por variante.
- Se asignan usuarios simulados por perfil:
  - `externo`: consultas de admisión/trámites
  - `administrativo`: consultas de proceso/operación
  - `academico`: consultas de contenido/tutores/investigación

### 4.3 Métricas de salida
- Globales:
  - Total de consultas, éxito, error, latencia promedio, p50, p95, p99
- Por dominio:
  - tasa de éxito, latencia promedio, ratio de match FAQ
- Por usuario/perfil:
  - distribución de latencia y éxito

## 5) Protocolo de ejecución recomendado
1. Levantar servicios (`run.sh --admin` o backend + cliente)
2. Ejecutar smoke test corto:
   - 30 consultas, 3 usuarios, concurrencia 3
3. Ejecutar corrida T1 principal:
   - 300 consultas, 12 usuarios, concurrencia 8
4. Ejecutar estrés moderado:
   - 500 consultas, 20 usuarios, concurrencia 10
5. Consolidar reportes CSV/JSON y comparar corridas.

## 6) Criterios mínimos para aprobar T1
- `success_rate >= 97%`
- `p95_latency_ms <= 8000`
- `error_rate <= 3%`
- `faq_match_ratio >= 70%` (según umbral configurado)

## 7) Archivos de evidencia generados
Por cada corrida se genera carpeta en `experiments/results/<run_id>/`:
- `detailed_results.csv`: una fila por consulta
- `summary.json`: resumen estadístico
- `config_used.json`: parámetros de ejecución (reproducibilidad)

## 8) Riesgos y mitigaciones
- Riesgo: variabilidad de LLM en respuestas largas.
  - Mitigación: evaluar similitud con normalización + extracción de bloque `Respuesta:`.
- Riesgo: carga inicial de modelo aumenta latencia inicial.
  - Mitigación: warmup previo (5 consultas de calentamiento).
- Riesgo: falsos negativos de similitud.
  - Mitigación: calibrar umbral por dominio (default 0.45).

## 9) Recomendación doctoral
Usar esta batería automática como evidencia cuantitativa principal para eficiencia/estabilidad y complementar con muestra humana controlada para claridad/satisfacción.