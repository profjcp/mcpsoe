# Experimentos T1 - SoeBOT

## Archivos
- `PLAN_EXPERIMENTAL_T1.md`: diseño metodológico y criterios de éxito.
- `run_battery.py`: script de batería automática (usuarios simulados + variantes de preguntas).
- `run_t1_suite.sh`: suite sugerida (smoke, principal, estrés moderado).

## Requisitos
1. Backend SoeBOT activo en `http://127.0.0.1:9000`
2. Entorno virtual activo (`venmcp`)

## Ejecución rápida (smoke)
```bash
source venmcp/bin/activate
python experiments/run_battery.py --requests 30 --users 3 --concurrency 3 --warmup 3
```

## Ejecución principal T1
```bash
source venmcp/bin/activate
python experiments/run_battery.py --requests 300 --users 12 --concurrency 8 --warmup 5
```

## Suite completa
```bash
chmod +x experiments/run_t1_suite.sh
./experiments/run_t1_suite.sh
```

## Salidas por corrida
Se crea una carpeta en `experiments/results/run_YYYYMMDD_HHMMSS/` con:
- `detailed_results.csv`
- `summary.json`
- `config_used.json`

## Métricas calculadas
- `success_rate`
- `auto_pass_rate`
- `faq_pattern_ratio`
- `latency_avg_ms`
- `latency_p95_ms`
- `latency_p99_ms`
- desglose por dominio

## Parámetros útiles
```bash
python experiments/run_battery.py --help
```
Parámetros clave:
- `--similarity-threshold` (default 0.45)
- `--overlap-threshold` (default 0.20)
- `--send-auto-feedback` (opcional, publica feedback sintético en `/feedback`)

## Nota metodológica
Estas baterías son válidas para eficiencia/estabilidad/exactitud automática y deben complementarse con muestra humana para claridad y satisfacción en tesis.