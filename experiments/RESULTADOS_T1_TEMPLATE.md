# Resultados Observados T1 - Plantilla para Tesis Doctoral

## 1) Metadatos del experimento

| Campo | Valor |
|---|---|
| Fecha de ejecución | [YYYY-MM-DD] |
| Run ID | [run_YYYYMMDD_HHMMSS] |
| Entorno | [Local / Servidor] |
| Versión de código (commit) | [hash_git] |
| URL backend | [http://127.0.0.1:9000] |
| Dataset fuente | [documentos/faq_*.txt] |
| Script | [experiments/run_battery.py] |

### Configuración usada (`config_used.json`)

| Parámetro | Valor |
|---|---|
| requests | [ ] |
| users | [ ] |
| concurrency | [ ] |
| seed | [ ] |
| timeout | [ ] |
| similarity_threshold | [ ] |
| overlap_threshold | [ ] |
| warmup | [ ] |
| send_auto_feedback | [true/false] |

---

## 2) Resultados globales

(Completar desde `summary.json` → `global_metrics`)

| Métrica | Valor observado | Umbral T1 | Cumple |
|---|---:|---:|---|
| total_requests | [ ] | N/A | N/A |
| success_rate | [ ] | >= 0.97 | [Sí/No] |
| auto_pass_rate | [ ] | >= 0.70 | [Sí/No] |
| faq_pattern_ratio | [ ] | >= 0.60 | [Sí/No] |
| latency_avg_ms | [ ] | Informativo | N/A |
| latency_median_ms | [ ] | Informativo | N/A |
| latency_p95_ms | [ ] | <= 8000 | [Sí/No] |
| latency_p99_ms | [ ] | <= 12000 (recomendado) | [Sí/No] |

---

## 3) Resultados por dominio

(Completar desde `summary.json` → `by_domain`)

| Dominio | Total | Success Rate | Auto Pass Rate | Latency Avg (ms) | Latency P95 (ms) |
|---|---:|---:|---:|---:|---:|
| AtencionCliente | [ ] | [ ] | [ ] | [ ] | [ ] |
| Academica | [ ] | [ ] | [ ] | [ ] | [ ] |
| Investigacion | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## 4) Análisis por perfil de usuario simulado

(Completar desde `detailed_results.csv` filtrando `user_type`)

| Perfil | # Consultas | Success Rate | Auto Pass Rate | Latency Avg (ms) | Latency P95 (ms) |
|---|---:|---:|---:|---:|---:|
| externo | [ ] | [ ] | [ ] | [ ] | [ ] |
| administrativo | [ ] | [ ] | [ ] | [ ] | [ ] |
| academico | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## 5) Casos críticos (evidencia cualitativa técnica)

(Extraer de `detailed_results.csv` donde `success=false` o `passed_auto_eval=false`)

| request_id | domain_expected | question_variant | http_status | latency_ms | similarity | overlap | error |
|---:|---|---|---:|---:|---:|---:|---|
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## 6) Contraste de hipótesis T1

### H1: `p95_latency_ms <= 8000`
- Valor observado: [ ]
- Decisión: [Se acepta / Se rechaza]
- Comentario: [ ]

### H2: `error_rate <= 3%`
- `error_rate = 1 - success_rate` = [ ]
- Decisión: [Se acepta / Se rechaza]
- Comentario: [ ]

### H3: `auto_pass_rate >= 70%`
- Valor observado: [ ]
- Decisión: [Se acepta / Se rechaza]
- Comentario: [ ]

### H4: estabilidad multiusuario (sin caída de servicio)
- Evidencia: [health checks / ausencia de fallas fatales]
- Decisión: [Se acepta / Se rechaza]
- Comentario: [ ]

---

## 7) Síntesis para capítulo de tesis

### 7.1 Hallazgos principales
1. [ ]
2. [ ]
3. [ ]

### 7.2 Limitaciones
- [ ]
- [ ]

### 7.3 Acciones de mejora para T2
- [ ]
- [ ]
- [ ]

---

## 8) Anexos
- Ruta del detalle: `experiments/results/[run_id]/detailed_results.csv`
- Ruta del resumen: `experiments/results/[run_id]/summary.json`
- Ruta de configuración: `experiments/results/[run_id]/config_used.json`

---

## Nota metodológica
Esta plantilla reporta evidencia automática válida para eficiencia, estabilidad y exactitud aproximada. Para claridad/satisfacción en tesis doctoral, complementar con evaluación humana controlada (grupo focal).