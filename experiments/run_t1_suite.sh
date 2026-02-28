#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
source venmcp/bin/activate

echo "=== SoeBOT T1 Suite: Smoke ==="
python experiments/run_battery.py \
  --base-url http://127.0.0.1:9000 \
  --requests 30 \
  --users 3 \
  --concurrency 3 \
  --seed 42 \
  --warmup 3

echo "=== SoeBOT T1 Suite: Principal ==="
python experiments/run_battery.py \
  --base-url http://127.0.0.1:9000 \
  --requests 300 \
  --users 12 \
  --concurrency 8 \
  --seed 42 \
  --warmup 5

echo "=== SoeBOT T1 Suite: Estres moderado ==="
python experiments/run_battery.py \
  --base-url http://127.0.0.1:9000 \
  --requests 500 \
  --users 20 \
  --concurrency 10 \
  --seed 42 \
  --warmup 5

echo "✅ Suite T1 finalizada. Revisa experiments/results/"
