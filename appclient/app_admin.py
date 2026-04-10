import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
from datetime import datetime

st.set_page_config(page_title="SoeBOT Admin Dashboard", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

    :root {
        --bg-1: #f7f1e8;
        --bg-2: #efe0c4;
        --ink: #1a1a1a;
        --panel: #fff7ea;
        --panel-strong: #f4dcc0;
        --accent: #e07a5f;
        --accent-2: #3d405b;
        --muted: #6e6e6e;
    }

    .stApp {
        background: radial-gradient(1200px 600px at 10% -10%, var(--bg-2) 0%, var(--bg-1) 45%, #ffffff 100%);
        color: var(--ink);
        font-family: 'Space Grotesk', sans-serif;
    }

    .app-title {
        font-size: 30px;
        font-weight: 700;
        letter-spacing: 0.2px;
        margin: 0 0 8px 0;
    }

    .app-subtitle {
        color: var(--muted);
        margin: 0 0 20px 0;
    }

    .panel {
        background: var(--panel);
        border: 1px solid #ead7c0;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.05);
        margin-bottom: 18px;
    }

    .panel-title {
        font-weight: 700;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='app-title'>Dashboard Administrativo - SoeBOT</div>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>Evidencia cuantitativa y cualitativa para validacion de tesis</div>", unsafe_allow_html=True)

# Función para obtener métricas
def get_metrics():
    try:
        response = requests.get("http://127.0.0.1:9000/metrics", timeout=5)
        return response.json()
    except Exception as e:
        st.error(f"Error conectando al servidor: {e}")
        return {}

def load_feedbacks():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    feedback_path = os.path.join(base_dir, "feedback.jsonl")
    feedbacks = []
    try:
        with open(feedback_path, "r") as f:
            for line in f:
                if line.strip():
                    feedbacks.append(json.loads(line))
    except FileNotFoundError:
        return []
    except Exception as e:
        st.warning(f"Error cargando feedback: {e}")
        return []
    return feedbacks


def load_interactions():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    interaction_path = os.path.join(base_dir, "interaction_logs.jsonl")
    interactions = []
    try:
        with open(interaction_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    interactions.append(json.loads(line))
    except FileNotFoundError:
        return []
    except Exception as e:
        st.warning(f"Error cargando interacciones: {e}")
        return []
    return interactions


def load_user_histories():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    histories_path = os.path.join(base_dir, "user_histories.json")
    try:
        with open(histories_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        st.warning(f"Error cargando historiales: {e}")
        return {}


def load_registered_users():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    users_path = os.path.join(base_dir, "users.json")
    try:
        with open(users_path, "r", encoding="utf-8") as f:
            return set(json.load(f).keys())
    except FileNotFoundError:
        return set()
    except Exception as e:
        st.warning(f"Error cargando usuarios registrados: {e}")
        return set()


def summarize_user_histories(user_histories):
    summary = {}
    for user_id, data in (user_histories or {}).items():
        conversations = data.get("conversations", []) or []
        active_id = data.get("active_id")
        total_questions = 0
        active_chat_title = "-"

        for conv in conversations:
            messages = conv.get("messages", []) or []
            total_questions += len(messages)
            if conv.get("id") == active_id:
                active_chat_title = conv.get("title", "-")

        if active_chat_title == "-" and conversations:
            active_chat_title = conversations[-1].get("title", "-")

        summary[user_id] = {
            "conversations": len(conversations),
            "historical_questions": total_questions,
            "active_chat": active_chat_title,
        }
    return summary


def download_dataframe(df, label, file_name):
    if df.empty:
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv, file_name, "text/csv")

# Refrescar datos
metrics = get_metrics()

if metrics:
    quant = metrics.get("quantitative", {})
    qual = metrics.get("qualitative", {})

    feedbacks = load_feedbacks()
    interactions = load_interactions()
    user_histories = load_user_histories()
    registered_users = load_registered_users()
    history_summary = summarize_user_histories(user_histories)

    df_feedbacks = pd.DataFrame(feedbacks) if feedbacks else pd.DataFrame()
    df_interactions = pd.DataFrame(interactions) if interactions else pd.DataFrame()

    if not df_feedbacks.empty:
        if "user_id" not in df_feedbacks.columns:
            df_feedbacks["user_id"] = "legacy"
        else:
            df_feedbacks["user_id"] = df_feedbacks["user_id"].fillna("legacy")

    if not df_interactions.empty:
        if "user_id" not in df_interactions.columns:
            df_interactions["user_id"] = "legacy"
        else:
            df_interactions["user_id"] = df_interactions["user_id"].fillna("legacy")
        if "response_time_s" in df_interactions.columns:
            df_interactions["response_time_s"] = pd.to_numeric(df_interactions["response_time_s"], errors="coerce")
        if "timestamp" in df_interactions.columns:
            df_interactions["timestamp"] = pd.to_datetime(df_interactions["timestamp"], errors="coerce")

    df_filtered = df_feedbacks.copy()
    df_interactions_filtered = df_interactions.copy()

    if not df_feedbacks.empty and "timestamp" in df_feedbacks.columns:
        df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"], errors="coerce")
        df_filtered = df_filtered.dropna(subset=["timestamp"]).sort_values("timestamp")
        if not df_filtered.empty:
            min_date = df_filtered["timestamp"].min().date()
            max_date = df_filtered["timestamp"].max().date()
            with st.expander("Filtros de analisis", expanded=False):
                date_range = st.date_input("Rango de fechas", (min_date, max_date))
                if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                    start_date, end_date = date_range
                    df_filtered = df_filtered[(df_filtered["timestamp"].dt.date >= start_date) & (df_filtered["timestamp"].dt.date <= end_date)]
                    if not df_interactions_filtered.empty and "timestamp" in df_interactions_filtered.columns:
                        df_interactions_filtered = df_interactions_filtered.dropna(subset=["timestamp"])
                        df_interactions_filtered = df_interactions_filtered[(df_interactions_filtered["timestamp"].dt.date >= start_date) & (df_interactions_filtered["timestamp"].dt.date <= end_date)]

    total_queries = int(quant.get("queries_total", 0))
    cache_hits = int(quant.get("cache_hits_total", 0))
    cache_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0
    avg_response = float(qual.get("avg_response_time", 0) or 0)
    avg_clarity = float(qual.get("avg_clarity", 0) or 0)
    avg_satisfaction = float(qual.get("avg_satisfaction", 0) or 0)
    avg_completeness = float(qual.get("avg_completeness", 0) or 0)
    halluc_rate = float(qual.get("hallucination_rate", 0) or 0) * 100
    veracity_score = max(0.0, 100.0 - halluc_rate)

    st.header("Resultados para validacion de tesis")

    st.subheader("Eficiencia")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Consultas", total_queries)
    col2.metric("Cache Hits", cache_hits)
    col3.metric("Cache Rate", f"{cache_rate:.1f}%")
    col4.metric("Tiempo medio (s)", f"{avg_response:.2f}")

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.bar(["Cache", "No Cache"], [cache_hits, max(total_queries - cache_hits, 0)], color=["#3d405b", "#e07a5f"])
    ax.set_title("Distribucion de respuestas cache vs no cache")
    ax.set_ylabel("Consultas")
    st.pyplot(fig)

    df_eff = pd.DataFrame([
        {"Indicador": "Consultas totales", "Valor": total_queries},
        {"Indicador": "Cache hits", "Valor": cache_hits},
        {"Indicador": "Cache rate (%)", "Valor": round(cache_rate, 2)},
        {"Indicador": "Tiempo promedio (s)", "Valor": round(avg_response, 2)}
    ])
    st.dataframe(df_eff, use_container_width=True)
    download_dataframe(df_eff, "Descargar eficiencia (CSV)", "eficiencia.csv")

    st.subheader("Claridad")
    col1, col2 = st.columns(2)
    col1.metric("Claridad promedio", f"{avg_clarity:.2f}/5")
    col2.metric("Completitud promedio", f"{avg_completeness:.2f}/5")

    if not df_filtered.empty and "clarity" in df_filtered.columns:
        clarity_counts = df_filtered["clarity"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.bar(clarity_counts.index.astype(str), clarity_counts.values, color="#3d405b")
        ax.set_title("Distribucion de claridad (1-5)")
        ax.set_xlabel("Puntaje")
        ax.set_ylabel("Respuestas")
        st.pyplot(fig)

        df_low_clarity = df_filtered[df_filtered["clarity"] <= 2][["timestamp", "question", "clarity", "comments"]].copy()
        if not df_low_clarity.empty:
            st.markdown("Casos con claridad baja (<=2)")
            st.dataframe(df_low_clarity, use_container_width=True)
            download_dataframe(df_low_clarity, "Descargar casos claridad baja", "claridad_baja.csv")

    st.subheader("Veracidad")
    col1, col2 = st.columns(2)
    col1.metric("Sin alucinaciones", f"{veracity_score:.1f}%")
    col2.metric("Errores totales", int(quant.get("errors_total", 0)))

    if qual.get("error_types"):
        df_errors = pd.DataFrame({
            "Tipo": list(qual["error_types"].keys()),
            "Frecuencia": list(qual["error_types"].values())
        })
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.bar(df_errors["Tipo"], df_errors["Frecuencia"], color="#e07a5f")
        ax.set_title("Errores detectados por tipo")
        ax.set_ylabel("Frecuencia")
        plt.xticks(rotation=30, ha="right")
        st.pyplot(fig)
        st.dataframe(df_errors, use_container_width=True)
        download_dataframe(df_errors, "Descargar errores", "errores.csv")

    st.subheader("Satisfaccion")
    col1, col2 = st.columns(2)
    col1.metric("Satisfaccion promedio", f"{avg_satisfaction:.2f}/5")
    col2.metric("Sentimiento promedio", f"{qual.get('avg_sentiment', 0):.2f}")

    if not df_filtered.empty and "satisfaction" in df_filtered.columns:
        df_trend = df_filtered.sort_values("timestamp")
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(df_trend["timestamp"], df_trend["satisfaction"], marker="o", linestyle="-", color="#3d405b")
        ax.axhline(y=3, color="#e07a5f", linestyle="--", label="Neutral (3)")
        ax.set_title("Tendencia de satisfaccion")
        ax.set_ylabel("Satisfaccion (1-5)")
        ax.set_xlabel("Fecha")
        ax.legend()
        st.pyplot(fig)

        df_low_sat = df_filtered[df_filtered["satisfaction"] <= 2][["timestamp", "question", "satisfaction", "comments"]].copy()
        if not df_low_sat.empty:
            st.markdown("Casos con satisfaccion baja (<=2)")
            st.dataframe(df_low_sat, use_container_width=True)
            download_dataframe(df_low_sat, "Descargar casos satisfaccion baja", "satisfaccion_baja.csv")
    
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
    
    # --- REPORTE GLOBAL Y POR USUARIO ---
    st.header("👥 Reporte Global y por Usuario")

    users_from_data = set(registered_users)
    users_from_data.update(history_summary.keys())
    persisted_user_ids = set()

    if not df_interactions_filtered.empty and "user_id" in df_interactions_filtered.columns:
        interaction_user_ids = set(df_interactions_filtered["user_id"].dropna().astype(str).tolist())
        users_from_data.update(interaction_user_ids)
        persisted_user_ids.update(interaction_user_ids)
    if not df_filtered.empty and "user_id" in df_filtered.columns:
        feedback_user_ids = set(df_filtered["user_id"].dropna().astype(str).tolist())
        users_from_data.update(feedback_user_ids)
        persisted_user_ids.update(feedback_user_ids)

    if users_from_data:
        selected_user = st.selectbox("Vista analítica", ["Global"] + sorted(users_from_data, key=lambda x: str(x).lower()))

        if selected_user == "Global":
            total_interactions = len(df_interactions_filtered) if not df_interactions_filtered.empty else 0
            avg_rt_global = round(df_interactions_filtered["response_time_s"].mean(), 2) if not df_interactions_filtered.empty and "response_time_s" in df_interactions_filtered.columns else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Usuarios registrados", len([u for u in registered_users if u != "legacy"]))
            col2.metric("Usuarios con historial", len([u for u in history_summary.keys() if u != "legacy"]))
            col3.metric("Interacciones persistidas", total_interactions)
            col4.metric("Tiempo medio global (s)", avg_rt_global)

            user_rows = []
            for user_id in sorted(users_from_data, key=lambda x: str(x).lower()):
                history_meta = history_summary.get(user_id, {})
                user_interactions = df_interactions_filtered[df_interactions_filtered["user_id"] == user_id] if not df_interactions_filtered.empty else pd.DataFrame()
                user_feedback = df_filtered[df_filtered["user_id"] == user_id] if not df_filtered.empty else pd.DataFrame()

                row = {
                    "user_id": user_id,
                    "registrado": "Sí" if user_id in registered_users else "No",
                    "conversaciones_guardadas": history_meta.get("conversations", 0),
                    "preguntas_historicas": history_meta.get("historical_questions", 0),
                    "interacciones_persistidas": len(user_interactions),
                    "feedbacks": len(user_feedback),
                    "tiempo_promedio_s": round(user_interactions["response_time_s"].mean(), 2) if not user_interactions.empty and "response_time_s" in user_interactions.columns else 0,
                    "chat_activo": history_meta.get("active_chat", "-"),
                }

                if not user_feedback.empty:
                    row["satisfaccion_promedio"] = round(user_feedback["satisfaction"].mean(), 2) if "satisfaction" in user_feedback.columns else 0
                    row["claridad_promedio"] = round(user_feedback["clarity"].mean(), 2) if "clarity" in user_feedback.columns else 0
                    row["completitud_promedio"] = round(user_feedback["completeness"].mean(), 2) if "completeness" in user_feedback.columns else 0

                user_rows.append(row)

            df_user_summary = pd.DataFrame(user_rows)
            st.dataframe(df_user_summary.fillna("-"), use_container_width=True)
            download_dataframe(df_user_summary.fillna(""), "Descargar reporte global por usuario", "reporte_global_por_usuario.csv")

            if "Direccion" in users_from_data:
                st.info("El perfil del director figura registrado como `Direccion` dentro del sistema.")
            if "legacy" in users_from_data:
                st.info("Los registros históricos previos sin user_id se muestran como 'legacy' y siguen contando para el análisis global.")
        else:
            history_meta = history_summary.get(selected_user, {"conversations": 0, "historical_questions": 0, "active_chat": "-"})
            user_interactions = df_interactions_filtered[df_interactions_filtered["user_id"] == selected_user] if not df_interactions_filtered.empty else pd.DataFrame()
            user_feedback = df_filtered[df_filtered["user_id"] == selected_user] if not df_filtered.empty else pd.DataFrame()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Chats guardados", history_meta.get("conversations", 0))
            col2.metric("Preguntas históricas", history_meta.get("historical_questions", 0))
            col3.metric("Interacciones persistidas", len(user_interactions))
            col4.metric("Feedbacks", len(user_feedback))

            col1, col2, col3 = st.columns(3)
            col1.metric("Tiempo medio (s)", round(user_interactions["response_time_s"].mean(), 2) if not user_interactions.empty and "response_time_s" in user_interactions.columns else 0)
            col2.metric("Satisfacción promedio", round(user_feedback["satisfaction"].mean(), 2) if not user_feedback.empty and "satisfaction" in user_feedback.columns else 0)
            col3.metric("Claridad promedio", round(user_feedback["clarity"].mean(), 2) if not user_feedback.empty and "clarity" in user_feedback.columns else 0)

            st.caption(f"Chat activo o más reciente: {history_meta.get('active_chat', '-')}")

            if not user_interactions.empty and "source" in user_interactions.columns:
                source_counts = user_interactions["source"].value_counts()
                fig, ax = plt.subplots(figsize=(7, 3))
                ax.bar(source_counts.index.astype(str), source_counts.values, color="#3d405b")
                ax.set_title(f"Fuentes de respuesta - {selected_user}")
                ax.set_ylabel("Interacciones")
                st.pyplot(fig)

            history_rows = []
            for conv in user_histories.get(selected_user, {}).get("conversations", []):
                for message in conv.get("messages", []):
                    if isinstance(message, list) and len(message) >= 2:
                        history_rows.append({
                            "chat": conv.get("title", "-"),
                            "pregunta": message[0],
                            "respuesta": str(message[1])[:180],
                            "tiempo_s": message[2] if len(message) > 2 else ""
                        })

            if history_rows:
                df_history = pd.DataFrame(history_rows[-20:])
                st.markdown("Historial reciente del usuario")
                st.dataframe(df_history, use_container_width=True)
                download_dataframe(df_history, f"Descargar historial de {selected_user}", f"historial_{selected_user}.csv")

            if not user_feedback.empty:
                display_user_columns = ["timestamp", "question", "satisfaction", "clarity", "completeness", "error_type", "comments"]
                df_user_display = user_feedback[display_user_columns].tail(15) if all(col in user_feedback.columns for col in display_user_columns) else user_feedback.tail(15)
                st.dataframe(df_user_display, use_container_width=True)
                download_dataframe(df_user_display, f"Descargar feedback de {selected_user}", f"feedback_{selected_user}.csv")

            if history_meta.get("historical_questions", 0) > 0 and selected_user not in persisted_user_ids:
                st.info("Este usuario sí tiene historial guardado, pero sus métricas detalladas pertenecen al sistema anterior. Desde ahora las nuevas interacciones ya quedarán segmentadas automáticamente.")
    else:
        st.info("Todavía no hay datos persistidos por usuario. Con nuevas pruebas quedarán registrados automáticamente.")

    # --- FEEDBACK DETALLADO ---
    st.header("💬 Feedback de Usuarios")
    if not df_filtered.empty:
        st.subheader("Feedback reciente")
        display_columns = ["timestamp", "user_id", "question", "satisfaction", "clarity", "completeness", "error_type", "comments"]
        df_display = df_filtered[display_columns].tail(15) if all(col in df_filtered.columns for col in display_columns) else df_filtered.tail(15)
        st.dataframe(df_display, use_container_width=True)
        download_dataframe(df_display, "Descargar feedback reciente", "feedback_reciente.csv")
    else:
        st.info("Sin feedback de usuarios aún.")
    
    # --- RESUMEN EJECUTIVO ---
    st.header("📋 Resumen Ejecutivo para Investigación")
    
    summary_text = f"""
    ### Métricas Clave para Tesis de Doctorado:
    
    **Eficiencia Administrativa:**
    - Total de consultas procesadas: **{int(quant.get('queries_total', 0))}**
    - Consultas resueltas por caché: **{int(quant.get('cache_hits_total', 0))}** (automático, sin latencia)
    - Porcentaje de automatización: **{round((int(quant.get('cache_hits_total', 0)) / max(1, int(quant.get('queries_total', 0)))) * 100, 1)}%**
    - Usuarios identificados en el histórico: **{len(set(df_interactions_filtered['user_id'])) if not df_interactions_filtered.empty and 'user_id' in df_interactions_filtered.columns else 0}**
    
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
