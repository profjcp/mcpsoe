import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

st.set_page_config(page_title="SoeBOT Admin Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard Administrativo - SoeBOT")
st.markdown("Monitoreo en tiempo real de métricas cuantitativas y cualitativas del sistema RAG")

# Función para obtener métricas
def get_metrics():
    try:
        response = requests.get("http://127.0.0.1:9000/metrics", timeout=5)
        return response.json()
    except Exception as e:
        st.error(f"Error conectando al servidor: {e}")
        return {}

# Refrescar datos
metrics = get_metrics()

if metrics:
    quant = metrics.get("quantitative", {})
    qual = metrics.get("qualitative", {})
    
    # --- MÉTRICAS CUANTITATIVAS ---
    st.header("📈 Métricas Cuantitativas (Prometheus)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔍 Consultas Totales", int(quant.get("queries_total", 0)))
    col2.metric("✅ Cache Hits", int(quant.get("cache_hits_total", 0)))
    col3.metric("❌ Errores", int(quant.get("errors_total", 0)))
    col4.metric("⚠️ Alucinaciones", int(quant.get("hallucinations_total", 0)))
    
    st.subheader("Recursos del Sistema")
    col1, col2 = st.columns(2)
    col1.metric("💻 CPU (%)", round(quant.get("cpu_usage_percent", 0), 1))
    col2.metric("🧠 Memoria (%)", round(quant.get("memory_usage_percent", 0), 1))
    
    # Visualización de recursos
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.bar(['CPU'], [quant.get("cpu_usage_percent", 0)], color='#1f77b4', alpha=0.7)
    ax1.set_ylim([0, 100])
    ax1.set_title("Uso de CPU (%)")
    ax1.axhline(y=80, color='r', linestyle='--', label='Alerta')
    
    ax2.bar(['Memoria'], [quant.get("memory_usage_percent", 0)], color='#ff7f0e', alpha=0.7)
    ax2.set_ylim([0, 100])
    ax2.set_title("Uso de Memoria (%)")
    ax2.axhline(y=80, color='r', linestyle='--', label='Alerta')
    st.pyplot(fig)
    
    # --- MÉTRICAS CUALITATIVAS ---
    st.header("✨ Métricas Cualitativas (Evaluación de Calidad)")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("😊 Satisfacción (1-5)", qual.get("avg_satisfaction", 0))
    col2.metric("💬 Claridad (1-5)", qual.get("avg_clarity", 0))
    col3.metric("✔️ Completitud (1-5)", qual.get("avg_completeness", 0))
    
    col1, col2, col3 = st.columns(3)
    halluc_rate = qual.get("hallucination_rate", 0) * 100
    col1.metric("🎯 Sin Alucinaciones (%)", f"{100 - halluc_rate:.1f}%")
    col2.metric("😌 Sentimiento Promedio", f"{qual.get('avg_sentiment', 0):.2f}", help="-1=Negativo, +1=Positivo")
    col3.metric("⏱️ Tiempo Respuesta Promedio (s)", qual.get("avg_response_time", 0))
    
    # --- DISTRIBUCIÓN DE PREGUNTAS POR CATEGORÍA ---
    st.subheader("📂 Distribución de Preguntas por Categoría")
    if qual.get("query_categories"):
        categories = list(qual["query_categories"].keys())
        counts = list(qual["query_categories"].values())
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(categories, counts, color='#2ca02c')
        ax.set_xlabel("Número de Preguntas")
        st.pyplot(fig)
        
        # Tabla de categorías
        df_categories = pd.DataFrame({
            "Categoría": categories,
            "Preguntas": counts,
            "Porcentaje (%)": [f"{(c/sum(counts)*100):.1f}%" for c in counts]
        })
        st.dataframe(df_categories, use_container_width=True)
    else:
        st.info("Sin categorías aún. Las consultas aparecerán después de las primeras interacciones.")
    
    # --- TIPOS DE ERROR ---
    st.subheader("⚠️ Tipos de Error Detectados")
    if qual.get("error_types"):
        errors = list(qual["error_types"].keys())
        error_counts = list(qual["error_types"].values())
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(errors, error_counts, color='#d62728')
        plt.xticks(rotation=45, ha='right')
        ax.set_ylabel("Frecuencia")
        st.pyplot(fig)
        
        df_errors = pd.DataFrame({
            "Tipo de Error": errors,
            "Frecuencia": error_counts
        })
        st.dataframe(df_errors, use_container_width=True)
    else:
        st.info("Sin errores reportados aún.")
    
    # --- FEEDBACK DETALLADO ---
    st.header("💬 Feedback de Usuarios")
    try:
        with open("../feedback.jsonl", "r") as f:
            feedbacks = []
            for line in f:
                if line.strip():
                    feedbacks.append(json.loads(line))
        
        if feedbacks:
            # Últimos 10 feedback
            recent_feedbacks = feedbacks[-10:]
            df_feedbacks = pd.DataFrame(recent_feedbacks)
            
            # Mostrar estadísticas de feedback
            st.subheader("Estadísticas de Feedback")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Feedback", len(feedbacks))
            col2.metric("Satisfacción Promedio", f"{df_feedbacks['satisfaction'].mean():.2f}/5")
            col3.metric("Claridad Promedio", f"{df_feedbacks['clarity'].mean():.2f}/5")
            
            # Tabla de feedback reciente
            st.subheader("Feedback Reciente (Últimos 10)")
            display_columns = ['timestamp', 'question', 'satisfaction', 'clarity', 'completeness', 'error_type', 'comments']
            if 'timestamp' in df_feedbacks.columns:
                df_display = df_feedbacks[display_columns].tail(10)
                st.dataframe(df_display, use_container_width=True)
            else:
                st.dataframe(df_feedbacks.tail(10), use_container_width=True)
            
            # Gráfico de satisfacción a lo largo del tiempo
            st.subheader("Tendencia de Satisfacción")
            df_feedbacks_sorted = pd.DataFrame(feedbacks).sort_values('timestamp')
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(range(len(df_feedbacks_sorted)), df_feedbacks_sorted['satisfaction'], marker='o', linestyle='-', color='#1f77b4')
            ax.axhline(y=3, color='orange', linestyle='--', label='Neutral (3)')
            ax.set_xlabel("Feedback Número")
            ax.set_ylabel("Satisfacción (1-5)")
            ax.set_title("Evolución de la Satisfacción del Usuario")
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
        else:
            st.info("Sin feedback de usuarios aún.")
    except FileNotFoundError:
        st.info("Archivo de feedback no encontrado. Los usuarios pueden enviar feedback desde el cliente principal.")
    except Exception as e:
        st.warning(f"Error cargando feedback: {e}")
    
    # --- RESUMEN EJECUTIVO ---
    st.header("📋 Resumen Ejecutivo para Investigación")
    
    summary_text = f"""
    ### Métricas Clave para Tesis de Doctorado:
    
    **Eficiencia Administrativa:**
    - Total de consultas procesadas: **{int(quant.get('queries_total', 0))}**
    - Consultas resueltas por caché: **{int(quant.get('cache_hits_total', 0))}** (automático, sin latencia)
    - Porcentaje de automatización: **{round((int(quant.get('cache_hits_total', 0)) / max(1, int(quant.get('queries_total', 0)))) * 100, 1)}%**
    
    **Calidad de Servicio:**
    - Satisfacción promedio del usuario: **{qual.get('avg_satisfaction', 0)}/5.0**
    - Claridad de respuestas: **{qual.get('avg_clarity', 0)}/5.0**
    - Completitud de respuestas: **{qual.get('avg_completeness', 0)}/5.0**
    - Tiempo de respuesta promedio: **{qual.get('avg_response_time', 0)} segundos**
    
    **Confiabilidad del Sistema:**
    - Porcentaje sin alucinaciones: **{100 - (qual.get('hallucination_rate', 0) * 100):.1f}%**
    - Sentimiento de respuestas (tono profesional): **{qual.get('avg_sentiment', 0):.2f}/1.0**
    - Errores detectados: **{int(quant.get('errors_total', 0))}**
    - Salud del sistema: ✅ **Operativo**
    
    **Cobertura de Contenidos:**
    - Categorías cubiertas: **{len(qual.get('query_categories', {}))}**
    - Tipos de error identificados: **{len(qual.get('error_types', {}))}**
    """
    st.markdown(summary_text)
    
    # Auto-refresh
    st.write("---")
    st.write(f"**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Botón de refresh manual
    if st.button("🔄 Actualizar Ahora"):
        st.rerun()
    
    # Auto-refresh cada 15 segundos (comentado, descomenta si quieres)
    # time.sleep(15)
    # st.rerun()
    
else:
    st.error("❌ No se pudieron obtener las métricas. Verifica que:")
    st.write("1. El servidor FastAPI esté corriendo (`python mcp_server_local.py`)")
    st.write("2. Ollama esté activo (`ollama serve`)")
    st.write("3. Redis esté corriendo (`redis-server`)")
    st.write("4. Se hayan hecho al menos algunas consultas desde el cliente principal")
