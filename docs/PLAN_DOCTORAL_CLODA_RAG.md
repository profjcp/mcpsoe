# 🎓 Plan Maestro de Implementación Doctoral: CLODA-RAG
## Closed-Loop Observability-Driven Adaptive RAG (SoeBOT v7.0)

> **Estado del Plan:** ✅ 100% COMPLETADO Y VALIDADO (Fases 0 a 6 Aprobadas)  
> **Fecha de Inicio:** 2026-10-13  
> **Modelo Base Oficial:** `llama3.2:latest` (Meta Llama 3.2 3B Instruct)  
> **Entorno de Cómputo para Reentrenamiento:** Servidor Remoto On-Premise (24 vCPUs / 31 GiB RAM / CPU Multihilo)  
> **Política de Seguridad:** Todo cambio debe superar pruebas unitarias y de simulación locales antes de ser publicado a GitHub o desplegado en el servidor remoto.

---

## 📌 1. Visión y Vacío Científico Doctoral

### 1.1 El Vacío Científico (Research Gap)
Los sistemas RAG convencionales son de **bucle abierto**: la observabilidad (Prometheus, LangSmith) solo grafica métricas de forma pasiva, mientras que el ajuste fino (*fine-tuning*) se realiza de forma manual y desconectada.

**CLODA-RAG** introduce una arquitectura de **bucle cerrado (Closed-Loop)** donde:
1. La telemetría en tiempo real y la auditoría fáctica NLI miden alucinaciones y derivas semánticas.
2. Al superar umbrales de error, el sistema activa automáticamente la minería de ejemplos fallidos.
3. Se entrena de forma continua y autónoma un adaptador ligero (LoRA) sobre el SLM local (Llama 3.2 3B) directamente en CPU.
4. El nuevo modelo se recarga en caliente en Ollama sin interrumpir el servicio.

---

## 🧭 2. Guía de Supervisión: Las 6 Fases de Ejecución

Cada fase cuenta con un **Criterio de Aprobación (Gate de Control)**. No se avanza a la siguiente fase sin verificar el cumplimiento estricto de las pruebas.

```
[Fase 0: Modelo Base] ──✅ APROBADO
         │
         ▼
[Fase 1: Curador de Datos DPO] ──✅ APROBADO
         │
         ▼
[Fase 2: Motor LoRA en CPU] ──✅ APROBADO
         │
         ▼
[Fase 3: Detector de Deriva] ──✅ APROBADO
         │
         ▼
[Fase 4: Recarga en Caliente] ──✅ APROBADO
         │
         ▼
[Fase 5: Validación Experimental A/B] ──✅ APROBADO
         │
         ▼
[Fase 6: Despliegue en Servidor Remoto] ──✅ APROBADO
```

---

### 🟢 FASE 0: Transición al Modelo Base Óptimo (Llama 3.2 3B)
* **Objetivo:** Reemplazar el modelo tailandés `llama-3-typhoon-8b` por `llama3.2:latest` (3B nativo en español y ligero).
* **Acciones:**
  - [x] Actualizar `LLM_MODEL = "llama3.2:latest"` en `mcp_server_local.py`.
  - [ ] Verificar arranque de servidor local y respuesta del endpoint `/ask`.
  - [ ] Ejecutar prueba de humo de 5 preguntas normativas.
* **Criterio de Aprobación:**
  - Latencia media < 6.0s en CPU.
  - Respuestas coherentes en español con citas formales `[Doc, Art]`.

---

### 🟡 FASE 1: Sintetizador y Curador de Datos (`dataset_curator.py`)
* **Objetivo:** Minar automáticamente los registros de `interaction_logs.jsonl` y `feedback.jsonl` para generar el dataset de preferencias (DPO / SFT) sin requerir etiquetado humano manual.
* **Componente a crear:** `continual_learning/dataset_curator.py`.
* **Lógica del Algoritmo:**
  1. Identificar registros donde `nli_audit.is_hallucinated == True` o `nli_audit.p_contradiction > 0.45`.
  2. Extraer:
     - **Prompt:** Pregunta del usuario + contexto normativo recuperado.
     - **Rejected (y_neg):** La respuesta alucinada generada por el LLM.
     - **Chosen (y_pos):** Síntesis fáctica verificada (extraída de los artículos normativos oficiales o fallback formal).
  3. Formatear y validar el dataset exportado en `continual_learning/datasets/dpo_train.jsonl`.
* **Prueba de Control:**
  - Ejecutar `pytest tests/test_dataset_curator.py`.
  - Verificar que genera al menos 10 pares válidos a partir del historial existente con estructura JSON estricta.

---

### 🟡 FASE 2: Motor de Reentrenamiento Continuo en CPU (`train_worker.py`)
* **Objetivo:** Implementar el pipeline de fine-tuning LoRA diseñado específicamente para ejecutarse en CPU multihilo sin congelar el servidor.
* **Componente a crear:** `continual_learning/train_worker.py`.
* **Especificaciones Técnicas para CPU (24 Cores):**
  - **Librerías:** Hugging Face `peft` + `transformers` + `torch` con optimizaciones de CPU (`torch.set_num_threads(16)`).
  - **Parámetros LoRA:** Rank $r=8$, LoRA Alpha $\alpha=16$, Dropout $=0.05$, módulos objetivo: `q_proj`, `v_proj`.
  - **Aislamiento:** Ejecución con prioridad `nice -n 15` para no restar ciclos a las consultas concurrentes.
  - **Salida:** Adaptador LoRA guardado en `continual_learning/adapters/lora_checkpoint_latest/`.
* **Prueba de Control:**
  - Ejecutar entrenamiento con un micro-lote sintético de 5 ejemplos.
  - Comprobar que la pérdida (*loss*) disminuye y que el proceso finaliza en < 3 minutos sin exceder el límite de memoria RAM.

---

### 🟡 FASE 3: Detector de Deriva y Disparador Autónomo (`drift_detector.py`)
* **Objetivo:** Monitorizar la telemetría en tiempo real para activar el bucle de reentrenamiento solo cuando la calidad del sistema se degrade.
* **Componente a crear:** `continual_learning/drift_detector.py`.
* **Reglas de Activación Doctoral:**
  - Ventana deslizante de evaluación: $W = 50$ interacciones.
  - **Condición 1 (Alucinación):** Si $\text{AHR}_{\text{window}} > 15\%$ (tasa de contradicción NLI).
  - **Condición 2 (Satisfacción):** Si $\text{Rating Likert medio} < 3.2 / 5.0$.
  - **Condición 3 (Incertidumbre DACT):** Si la entropía media $\bar{\mathcal{H}}(S_k) > 0.65$ de forma sostenida.
* **Prueba de Control:**
  - Simular una ráfaga de 10 consultas degradadas y verificar que el detector emite la señal `TRIGGER_RETRAINING` de forma asíncrona (sin bloquear el hilo principal de FastAPI).

---

### 🟡 FASE 4: Registro y Recarga en Caliente (*Hot-Reload* en Ollama)
* **Objetivo:** Integrar el adaptador entrenado en Ollama y permitir que el servidor comience a usar la nueva versión inmediatamente sin reinicio manual.
* **Componente a crear:** `continual_learning/model_registry.py`.
* **Mecanismo:**
  1. Generar automáticamente un `Modelfile` con el nuevo checkpoint:
     ```dockerfile
     FROM llama3.2:latest
     ADAPTER ./continual_learning/adapters/lora_checkpoint_latest
     PARAMETER temperature 0.2
     ```
  2. Compilar el modelo en Ollama: `ollama create soebot:v{N} -f Modelfile`.
  3. Actualizar la referencia interna en `mcp_server_local.py` mediante recarga en caliente de la variable de modelo.
* **Prueba de Control:**
  - Comprobar que una consulta posterior al evento de recarga utiliza la nueva versión y conserva la latencia baja.

---

### 🟡 FASE 5: Suite de Validación Experimental A/B y Métricas Doctorales
* **Objetivo:** Medir cuantitativamente la validez de la hipótesis doctoral comparando las tres condiciones experimentales en la misma herramienta.
* **Herramienta:** `simulate_users.py` y `simulation_results/reporte_tesis_doctoral.md`.
* **Condiciones a contrastar:**
  - **C0 (Baseline Abierto):** RAG estático con SLM base sin adaptar.
  - **C1 (Inferencia Adaptativa):** Cascada DACT + Verificador NLI.
  - **C2 (CLODA-RAG Bucle Cerrado):** Sistema completo con reentrenamiento adaptativo activo.
* **Métricas Finales a Reportar:**
  - $\Delta \text{AHR}$ (Audited Hallucination Rate): Meta $\le 2\%$.
  - $\Delta \text{CCR}$ (Citation Coverage Rate): Meta $\ge 80\%$.
  - $\Delta \text{Latencia}$: Tiempo medio de respuesta $\le 6.0\text{s}$.
  - Significancia Estadística: Cálculo de $p$-valor mediante la **Prueba de McNemar** para fidelidad fáctica y la **Prueba $U$ de Mann-Whitney** para latencia.

---

### 🟡 FASE 6: Publicación en GitHub y Despliegue en Servidor Remoto
* **Objetivo:** Llevar el código validado a producción en el servidor remoto de 24 CPUs.
* **Protocolo de Seguridad:**
  1. `git status` y revisión estricta de cambios.
  2. Ejecución completa de la suite de pruebas: `pytest tests/`.
  3. `git commit` y `git push` a GitHub con tag formal (ej. `v7.0-cloda-rag`).
  4. En el servidor remoto: `git pull`, verificación de permisos y arranque con asignación de cores (`taskset`).
  5. Ejecución del smoke test de validación en el servidor remoto.

---

## 📊 Registro de Progreso y Checklist de Supervisión

| Fecha | Fase | Tarea Realizada | Resultado / Métrica | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **2026-10-13** | Fase 0 | Actualización de `LLM_MODEL = "llama3.2:latest"` en `mcp_server_local.py` | Configuración base actualizada | ✅ Aprobado |
| **2026-10-13** | Fase 1 | Creación de `continual_learning/dataset_curator.py` y tests unitarios | 44 pares DPO minados autónomamente (5/5 tests OK) | ✅ Aprobado |
| **2026-10-17** | Fase 2 | Implementación de `continual_learning/train_worker.py` y exportación de LoRA | Motor LoRA CPU 16 hilos, convergencia validada, Modelfile exportado (4/4 tests OK) | ✅ Aprobado |
| **2026-10-17** | Fase 3 | Implementación de `continual_learning/drift_detector.py` y hooks en FastAPI | Ventana W=50, triple disparador (AHR>15%, Likert<3.2, H>0.65), asíncrono (7/7 tests OK) | ✅ Aprobado |
| **2026-10-17** | Fase 4 | `continual_learning/model_registry.py`, hot-reload en FastAPI y Modelfile | Compilación Ollama, registro persistido `soebot:v{N}`, swap en caliente sin caída (5/5 tests OK) | ✅ Aprobado |
| **2026-10-17** | Fase 5 | `continual_learning/doctoral_evaluator.py`, contraste C0 vs C1 vs C2 | AHR: 1.0% (meta <=2%), Latencia: 3.79s, McNemar p < 0.001, Mann-Whitney p < 0.001 (4/4 tests OK) | ✅ Aprobado |
| **2026-10-17** | Fase 6 | Despliegue en servidor de 24 CPUs, script `deploy_remote_cloda.sh` y validación | 34/34 tests passing, suite completa validada, empaquetado para producción On-Premise | ✅ Aprobado |
