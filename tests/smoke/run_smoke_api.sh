#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:9000}"
RESULTS_DIR="tests/results"
RAW_DIR="${RESULTS_DIR}/curl_raw"
OUT_FILE="${RESULTS_DIR}/smoke_api_latest.md"

mkdir -p "${RESULTS_DIR}" "${RAW_DIR}"

ts="$(date -Iseconds)"

echo "# Smoke API Results" > "${OUT_FILE}"
echo "" >> "${OUT_FILE}"
echo "- Timestamp: ${ts}" >> "${OUT_FILE}"
echo "- Base URL: ${BASE_URL}" >> "${OUT_FILE}"
echo "" >> "${OUT_FILE}"

run_case() {
  local name="$1"
  local method="$2"
  local path="$3"
  local data="${4:-}"
  local raw_file="${RAW_DIR}/$(echo "$name" | tr ' ' '_' | tr -cd '[:alnum:]_').json"

  echo "## ${name}" >> "${OUT_FILE}"
  if [[ -n "${data}" ]]; then
    response="$(curl -sS -X "${method}" "${BASE_URL}${path}" -H "Content-Type: application/json" -d "${data}")"
  else
    response="$(curl -sS -X "${method}" "${BASE_URL}${path}")"
  fi

  echo "${response}" > "${raw_file}"
  echo '```json' >> "${OUT_FILE}"
  echo "${response}" | head -c 1200 >> "${OUT_FILE}"
  echo "" >> "${OUT_FILE}"
  echo '```' >> "${OUT_FILE}"
  echo "" >> "${OUT_FILE}"
}

run_case "Health" "GET" "/health"
run_case "Ask Guidance" "POST" "/ask" '{"question":"hola","user_id":"smoke_guidance"}'
run_case "Ask FAQ" "POST" "/ask" '{"question":"¿Cuáles son los documentos de inscripción?","user_id":"smoke_faq"}'
run_case "Ask Cache Repeat" "POST" "/ask" '{"question":"¿Cuáles son los documentos de inscripción?","user_id":"smoke_faq"}'
run_case "Ask RAG DOC" "POST" "/ask" '{"question":"Explica la diferencia entre plan de estudios y malla curricular","user_id":"smoke_rag"}'
run_case "Feedback OK" "POST" "/feedback" '{"question":"¿Cuáles son los documentos de inscripción?","response":"respuesta de prueba","user_id":"smoke_feedback","satisfaction":5,"clarity":4,"completeness":4,"error_type":"","comments":"ok"}'
run_case "Metrics" "GET" "/metrics"

echo "## Ask Invalid Payload (expect 422)" >> "${OUT_FILE}"
invalid_resp="$(curl -sS -o /tmp/smoke_invalid_resp.json -w "%{http_code}" -X POST "${BASE_URL}/ask" -H "Content-Type: application/json" -d '{"user_id":"smoke_invalid"}')"
echo "- HTTP status: ${invalid_resp}" >> "${OUT_FILE}"
echo '```json' >> "${OUT_FILE}"
cat /tmp/smoke_invalid_resp.json >> "${OUT_FILE}"
echo "" >> "${OUT_FILE}"
echo '```' >> "${OUT_FILE}"
echo "" >> "${OUT_FILE}"

echo "Smoke API completed. Report: ${OUT_FILE}"
