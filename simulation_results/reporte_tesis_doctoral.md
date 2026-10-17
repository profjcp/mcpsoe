# 🎓 Reporte Experimental Consolidado - Tesis Doctoral
## Closed-Loop Observability-Driven Adaptive RAG (CLODA-RAG)
> **Fecha de Emisión:** 2026-10-17T12:17:29.069417  
> **Muestra Experimental:** $N = 100$ consultas normativas académicas  
> **Modelo Base:** `llama3.2:latest` (Meta Llama 3.2 3B Instruct)  
> **Nivel de Confianza Estadístico:** $1 - \alpha = 95\%$ (Significancia crítica $\alpha = 0.05$)

---

## 📌 1. Contraste Cuantitativo de las 3 Condiciones Experimentales

| Dimensión / Indicador Doctoral | Símbolo | C0: Baseline Abierto | C1: Inferencia Adaptativa (DACT+NLI) | C2: CLODA-RAG Bucle Cerrado | Meta Tesis | Estado Doctoral |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cumplimiento Políticas Acceso** | $\text{APCR}$ | **100.0%** | **100.0%** | **100.0%** | $100.0\%$ | ✅ Aprobado |
| **Tasa de Alucinación Auditada** | $\text{AHR}$ | 46.0% | 12.0% | **1.0%** | $\le 2.0\%$ | ✅ Cumplido |
| **Tasa de Cobertura de Citas** | $\text{CCR}$ | 0.0% | 100.0% | **99.0%** | $\ge 80.0\%$ | ✅ Cumplido |
| **Tasa Contingencia Factual** | $\text{CFR}$ | 0.0% | 0.0% | **0.0%** | Formal | ✅ Honesto |
| **Latencia Media Total** | $\bar{T}$ | 36.40s | 20.02s | **3.79s** | $\le 6.0\text{s}$ | ✅ Ultrarrápido |
| **Mediana de Latencia** | $\tilde{T}$ | 60.06s | 33.03s | **3.80s** | $\le 5.0\text{s}$ | ✅ Eficiente |
| **Time-to-First-Token Medio** | $\text{TTFT}$ | 10.19s | 4.40s | **0.68s** | $\le 1.5\text{s}$ | ✅ Fluido |

---

## 🔬 2. Validación de Hipótesis y Pruebas de Significancia Estadística

### 2.1 Hipótesis H1c: Fidelidad Fáctica y Reducción de Alucinaciones
* **Contraste:** $H_0: \text{AHR}_{C2} = \text{AHR}_{C0}$ vs $H_1: \text{AHR}_{C2} < \text{AHR}_{C0}$
* **Prueba Estadística:** Prueba de McNemar con Corrección de Continuidad de Edwards.
* **Estadístico $\chi^2$:** **43.0222** (grados de libertad $df = 1$).
* **Valor $p$:** **0.000000** (Significativo al nivel $\alpha = 0.05$: **True**).
* **Conclusión Científica:** Se rechaza $H_0$ con un nivel de confianza $> 99.9\%$. El bucle cerrado adaptativo reduce drásticamente las alucinaciones de $46.0\%$ a **$1.0\%$**.

### 2.2 Hipótesis H1a: Eficiencia Computacional y Latencia en CPU
* **Contraste:** $H_0: T_{C2} \ge T_{C0}$ vs $H_1: T_{C2} < T_{C0}$
* **Prueba Estadística:** Mann-Whitney $U$ para muestras independientes no paramétricas.
* **Estadístico $U$:** **6400.0**.
* **Valor $p$:** **0.000617** (Significativo al nivel $\alpha = 0.05$: **True**).
* **Conclusión Científica:** Se rechaza $H_0$. El cambio al SLM ligero 3B optimizado con LoRA y atajo DACT reduce el tiempo medio de respuesta en **32.61s** (mejora de velocidad de ~89%).

### 2.3 Contribución Específica del Reentrenamiento Continuo (C1 vs C2)
* **Estadístico McNemar (C1 $\to$ C2):** $\chi^2 = 9.0909$, $p = 0.002569$.
* **Delta Cobertura de Citas ($\Delta \text{CCR}$):** Incremento de **+-1.0%**, alcanzando **99.0%** de citas normativas estrictas `[Doc, Art]` generadas sin instrucciones repetitivas.

---

## 🏛️ 3. Ecuaciones Matemáticas Validadas en el Experimento

1. **Cumplimiento de Políticas de Acceso (APCR):**
   $$\text{APCR} = \frac{\sum_{i=1}^N \mathbb{I}(\text{nivel\_acceso}_{\text{chunk}, i} \le \text{nivel\_acceso}_{\text{usuario}, i})}{N} = 100.0\%$$
2. **Tasa de Alucinación Auditada (AHR):**
   $$\text{AHR} = \frac{\sum_{i=1}^N \mathbb{I}(\text{NLI\_Contradiction}_i > 0.45)}{N} = 1.0\%$$
3. **Tasa de Cobertura de Citas (CCR):**
   $$\text{CCR} = \frac{\sum_{i=1}^N \mathbb{I}(\text{Respuesta}_i \text{ contiene } [\text{Doc, Art}])}{N} = 99.0\%$$

---

## 📋 4. Veredicto Final del Gate de Control (Fase 5)

> **Dictamen:** **APROBADO CON DISTINCIÓN.** Todos los indicadores experimentales superan los umbrales definidos en el Plan Maestro Doctoral. El sistema se encuentra científicamente validado y listo para la Fase 6 (Despliegue en Servidor Remoto On-Premise).
