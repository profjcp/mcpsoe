import ast
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
        --bg-1: #ffffff;
        --bg-2: #ffffff;
        --ink: #111111;
        --panel: #ffffff;
        --panel-strong: #ffffff;
        --accent: #111111;
        --accent-2: #111111;
        --muted: #6b7280;
        --line: #e5e7eb;
        --hover: #f3f4f6;
    }

    .stApp {
        background: #ffffff;
        color: var(--ink);
        font-family: 'Space Grotesk', sans-serif;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background: #ffffff !important;
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
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px;
        box-shadow: none;
        margin-bottom: 18px;
    }

    .panel-title {
        font-weight: 700;
        margin-bottom: 8px;
    }

    /* Scroll horizontal para barra de pestañas cuando hay muchas */
    div[data-testid="stTabs"] > div[role="tablist"] {
        overflow-x: auto;
        overflow-y: hidden;
        flex-wrap: nowrap;
        white-space: nowrap;
        scrollbar-width: thin;
        scrollbar-color: #cbd5e1 #f1f5f9;
        padding-bottom: 4px;
    }

    div[data-testid="stTabs"] > div[role="tablist"]::-webkit-scrollbar {
        height: 8px;
    }

    div[data-testid="stTabs"] > div[role="tablist"]::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 999px;
    }

    div[data-testid="stTabs"] > div[role="tablist"]::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 999px;
    }

    div[data-testid="stTabs"] button[role="tab"] {
        flex: 0 0 auto;
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


def parse_category_values(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except (ValueError, SyntaxError):
                pass
        return [text]
    return [str(value).strip()]


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
        if "timestamp" in df_feedbacks.columns:
            df_feedbacks["timestamp"] = pd.to_datetime(df_feedbacks["timestamp"], errors="coerce")
        for col in ["satisfaction", "clarity", "completeness"]:
            if col in df_feedbacks.columns:
                df_feedbacks[col] = pd.to_numeric(df_feedbacks[col], errors="coerce")

    if not df_interactions.empty:
        if "user_id" not in df_interactions.columns:
            df_interactions["user_id"] = "legacy"
        else:
            df_interactions["user_id"] = df_interactions["user_id"].fillna("legacy")
        if "response_time_s" in df_interactions.columns:
            df_interactions["response_time_s"] = pd.to_numeric(df_interactions["response_time_s"], errors="coerce")
        if "timestamp" in df_interactions.columns:
            df_interactions["timestamp"] = pd.to_datetime(df_interactions["timestamp"], errors="coerce")
        if "categories" not in df_interactions.columns:
            df_interactions["categories"] = [[] for _ in range(len(df_interactions))]
        df_interactions["categories_list"] = df_interactions["categories"].apply(parse_category_values)
        df_interactions["category_label"] = df_interactions["categories_list"].apply(lambda values: ", ".join(values) if values else "Sin categoría")

    users_from_data = set(registered_users)
    users_from_data.update(history_summary.keys())
    if not df_interactions.empty and "user_id" in df_interactions.columns:
        users_from_data.update(df_interactions["user_id"].dropna().astype(str).tolist())
    if not df_feedbacks.empty and "user_id" in df_feedbacks.columns:
        users_from_data.update(df_feedbacks["user_id"].dropna().astype(str).tolist())

    all_dates = []
    if not df_interactions.empty and "timestamp" in df_interactions.columns:
        valid_dates = df_interactions["timestamp"].dropna()
        if not valid_dates.empty:
            all_dates.extend(valid_dates.dt.date.tolist())
    if not df_feedbacks.empty and "timestamp" in df_feedbacks.columns:
        valid_dates = df_feedbacks["timestamp"].dropna()
        if not valid_dates.empty:
            all_dates.extend(valid_dates.dt.date.tolist())

    if all_dates:
        default_start = min(all_dates)
        default_end = max(all_dates)
    else:
        default_start = datetime.now().date()
        default_end = datetime.now().date()

    user_options = sorted(users_from_data, key=lambda x: str(x).lower())
    if not df_interactions.empty and "source" in df_interactions.columns:
        df_interactions["source"] = df_interactions["source"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    source_options = sorted(df_interactions["source"].dropna().astype(str).unique().tolist()) if not df_interactions.empty and "source" in df_interactions.columns else []
    category_options = sorted({category for values in (df_interactions["categories_list"] if not df_interactions.empty and "categories_list" in df_interactions.columns else []) for category in values})

    st.sidebar.header("Filtros de análisis")
    st.sidebar.caption("Reduce el ruido visual y analiza solo el subconjunto que te interesa.")
    date_range = st.sidebar.date_input("Rango de fechas", (default_start, default_end))
    selected_users = st.sidebar.multiselect("Usuarios", user_options, default=user_options)
    selected_sources = st.sidebar.multiselect("Fuentes de respuesta", source_options, default=source_options)
    selected_categories = st.sidebar.multiselect("Categorías", category_options, default=category_options)
    feedback_scope = st.sidebar.selectbox("Estado de feedback", ["Todos", "Solo con feedback", "Solo sin feedback"])
    keyword = st.sidebar.text_input("Buscar texto", placeholder="Ej.: tutor, Moodle, defensa")

    df_feedbacks_view = df_feedbacks.copy()
    df_interactions_view = df_interactions.copy()

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
        if not df_feedbacks_view.empty and "timestamp" in df_feedbacks_view.columns:
            df_feedbacks_view = df_feedbacks_view.dropna(subset=["timestamp"])
            df_feedbacks_view = df_feedbacks_view[(df_feedbacks_view["timestamp"].dt.date >= start_date) & (df_feedbacks_view["timestamp"].dt.date <= end_date)]
        if not df_interactions_view.empty and "timestamp" in df_interactions_view.columns:
            df_interactions_view = df_interactions_view.dropna(subset=["timestamp"])
            df_interactions_view = df_interactions_view[(df_interactions_view["timestamp"].dt.date >= start_date) & (df_interactions_view["timestamp"].dt.date <= end_date)]

    if user_options and len(selected_users) != len(user_options):
        selected_user_set = set(selected_users)
        if not df_feedbacks_view.empty and "user_id" in df_feedbacks_view.columns:
            df_feedbacks_view = df_feedbacks_view[df_feedbacks_view["user_id"].isin(selected_user_set)]
        if not df_interactions_view.empty and "user_id" in df_interactions_view.columns:
            df_interactions_view = df_interactions_view[df_interactions_view["user_id"].isin(selected_user_set)]

    if source_options and len(selected_sources) != len(source_options) and not df_interactions_view.empty:
        df_interactions_view = df_interactions_view[df_interactions_view["source"].isin(selected_sources)]

    if category_options and len(selected_categories) != len(category_options) and not df_interactions_view.empty:
        selected_category_set = set(selected_categories)
        df_interactions_view = df_interactions_view[df_interactions_view["categories_list"].apply(lambda values: any(category in selected_category_set for category in values))]

    if keyword.strip():
        term = keyword.strip().lower()
        if not df_interactions_view.empty:
            interaction_mask = df_interactions_view["question"].astype(str).str.lower().str.contains(term, na=False)
            if "response_preview" in df_interactions_view.columns:
                interaction_mask = interaction_mask | df_interactions_view["response_preview"].astype(str).str.lower().str.contains(term, na=False)
            df_interactions_view = df_interactions_view[interaction_mask]
        if not df_feedbacks_view.empty:
            feedback_mask = df_feedbacks_view["question"].astype(str).str.lower().str.contains(term, na=False)
            if "comments" in df_feedbacks_view.columns:
                feedback_mask = feedback_mask | df_feedbacks_view["comments"].astype(str).str.lower().str.contains(term, na=False)
            df_feedbacks_view = df_feedbacks_view[feedback_mask]

    if feedback_scope != "Todos":
        users_with_feedback = set(df_feedbacks_view["user_id"].dropna().astype(str).tolist()) if not df_feedbacks_view.empty else set()
        if feedback_scope == "Solo con feedback":
            if not df_interactions_view.empty:
                df_interactions_view = df_interactions_view[df_interactions_view["user_id"].isin(users_with_feedback)]
        else:
            if not df_interactions_view.empty:
                df_interactions_view = df_interactions_view[~df_interactions_view["user_id"].isin(users_with_feedback)]

    filtered_user_options = sorted(set(df_interactions_view["user_id"].dropna().astype(str).tolist()) | set(df_feedbacks_view["user_id"].dropna().astype(str).tolist()) | set(selected_users or []), key=lambda x: str(x).lower())
    if not filtered_user_options:
        filtered_user_options = user_options

    view_total_queries = len(df_interactions_view) if not df_interactions_view.empty else 0
    history_total_queries = sum(history_summary.get(user_id, {}).get("historical_questions", 0) for user_id in filtered_user_options)
    visible_users = len(set(df_interactions_view["user_id"].dropna().astype(str).tolist())) if not df_interactions_view.empty else 0
    feedback_count = len(df_feedbacks_view) if not df_feedbacks_view.empty else 0
    avg_response = round(df_interactions_view["response_time_s"].dropna().mean(), 2) if not df_interactions_view.empty and "response_time_s" in df_interactions_view.columns and not df_interactions_view["response_time_s"].dropna().empty else 0
    avg_satisfaction = round(df_feedbacks_view["satisfaction"].dropna().mean(), 2) if not df_feedbacks_view.empty and "satisfaction" in df_feedbacks_view.columns and not df_feedbacks_view["satisfaction"].dropna().empty else 0
    avg_clarity = round(df_feedbacks_view["clarity"].dropna().mean(), 2) if not df_feedbacks_view.empty and "clarity" in df_feedbacks_view.columns and not df_feedbacks_view["clarity"].dropna().empty else 0
    avg_completeness = round(df_feedbacks_view["completeness"].dropna().mean(), 2) if not df_feedbacks_view.empty and "completeness" in df_feedbacks_view.columns and not df_feedbacks_view["completeness"].dropna().empty else 0
    cache_hits = int((df_interactions_view["source"] == "CACHE").sum()) if not df_interactions_view.empty and "source" in df_interactions_view.columns else 0
    faq_hits = int((df_interactions_view["source"] == "FAQ").sum()) if not df_interactions_view.empty and "source" in df_interactions_view.columns else 0
    guidance_hits = int((df_interactions_view["source"] == "GUIDANCE").sum()) if not df_interactions_view.empty and "source" in df_interactions_view.columns else 0
    cache_rate = round((cache_hits / view_total_queries) * 100, 1) if view_total_queries else 0
    hallucination_rate = round((df_interactions_view["hallucinated"].fillna(False).astype(bool).sum() / view_total_queries) * 100, 1) if not df_interactions_view.empty and "hallucinated" in df_interactions_view.columns and view_total_queries else 0
    source_counts = df_interactions_view["source"].value_counts() if not df_interactions_view.empty and "source" in df_interactions_view.columns else pd.Series(dtype="int64")
    top_source = source_counts.idxmax() if not source_counts.empty else "Sin datos"

    user_rows = []
    for user_id in filtered_user_options:
        history_meta = history_summary.get(user_id, {})
        user_interactions = df_interactions_view[df_interactions_view["user_id"] == user_id] if not df_interactions_view.empty else pd.DataFrame()
        user_feedback = df_feedbacks_view[df_feedbacks_view["user_id"] == user_id] if not df_feedbacks_view.empty else pd.DataFrame()
        user_rows.append({
            "user_id": user_id,
            "registrado": "Sí" if user_id in registered_users else "No",
            "consultas_en_vista": len(user_interactions),
            "preguntas_historicas_totales": history_meta.get("historical_questions", 0),
            "conversaciones_guardadas": history_meta.get("conversations", 0),
            "feedbacks": len(user_feedback),
            "tiempo_promedio_s": round(user_interactions["response_time_s"].dropna().mean(), 2) if not user_interactions.empty and "response_time_s" in user_interactions.columns and not user_interactions["response_time_s"].dropna().empty else 0,
            "satisfaccion_promedio": round(user_feedback["satisfaction"].dropna().mean(), 2) if not user_feedback.empty and "satisfaction" in user_feedback.columns and not user_feedback["satisfaction"].dropna().empty else 0,
            "claridad_promedio": round(user_feedback["clarity"].dropna().mean(), 2) if not user_feedback.empty and "clarity" in user_feedback.columns and not user_feedback["clarity"].dropna().empty else 0,
            "completitud_promedio": round(user_feedback["completeness"].dropna().mean(), 2) if not user_feedback.empty and "completeness" in user_feedback.columns and not user_feedback["completeness"].dropna().empty else 0,
            "chat_activo": history_meta.get("active_chat", "-")
        })

    df_user_summary = pd.DataFrame(user_rows).sort_values(["consultas_en_vista", "preguntas_historicas_totales"], ascending=False) if user_rows else pd.DataFrame()

    st.header("Dashboard analítico para tesis")
    st.caption("Vista reorganizada para explorar métricas cuantitativas y cualitativas sin saturar la pantalla.")

    with st.expander("Criterios activos", expanded=False):
        st.markdown(f"""
        - **Fechas:** {default_start if not isinstance(date_range, (list, tuple)) or len(date_range) != 2 else date_range[0]} a {default_end if not isinstance(date_range, (list, tuple)) or len(date_range) != 2 else date_range[1]}
        - **Usuarios seleccionados:** {', '.join(selected_users) if selected_users else 'Ninguno'}
        - **Fuentes:** {', '.join(selected_sources) if selected_sources else 'Todas'}
        - **Categorías:** {', '.join(selected_categories) if selected_categories else 'Todas'}
        - **Estado de feedback:** {feedback_scope}
        - **Búsqueda por texto:** {keyword if keyword.strip() else 'Sin filtro'}
        """)

    tab_resumen, tab_quant, tab_qual, tab_users, tab_routing, tab_method, tab_ragas, tab_data = st.tabs([
        "📌 Res.",
        "📈 Cuant.",
        "✨ Cual.",
        "👤 Usrs",
        "🧭 Routing",
        "🧮 Método",
        "🧪 RAGAS",
        "🗂️ Datos"
    ])

    with tab_resumen:
        st.subheader("Resumen ejecutivo")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Consultas en vista", view_total_queries)
        col2.metric("Usuarios visibles", visible_users)
        col3.metric("Tiempo medio (s)", avg_response)
        col4.metric("Feedbacks", feedback_count)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Satisfacción media", f"{avg_satisfaction}/5")
        col2.metric("Claridad media", f"{avg_clarity}/5")
        col3.metric("Completitud media", f"{avg_completeness}/5")
        col4.metric("Sin alucinaciones", f"{100 - hallucination_rate:.1f}%")

        narrative = (
            f"Con los filtros actuales se observan **{view_total_queries} interacciones** y **{visible_users} usuarios** en la vista analítica. "
            f"La fuente predominante es **{top_source}** y el tiempo promedio de respuesta es **{avg_response} s**. "
            f"Además, el histórico acumulado de los usuarios visibles alcanza **{history_total_queries} consultas**, útil para el análisis longitudinal de la tesis."
        )
        st.info(narrative)

        col1, col2 = st.columns(2)
        with col1:
            if not source_counts.empty:
                fig, ax = plt.subplots(figsize=(7, 3.5))
                ax.bar(source_counts.index.astype(str), source_counts.values, color=["#3d405b", "#e07a5f", "#81b29a", "#f2cc8f", "#6d597a"][:len(source_counts)])
                ax.set_title("Distribución por fuente de respuesta")
                ax.set_ylabel("Interacciones")
                plt.xticks(rotation=25, ha="right")
                st.pyplot(fig)
            else:
                st.info("No hay interacciones suficientes para mostrar la distribución por fuente.")

        with col2:
            if not df_interactions_view.empty and "timestamp" in df_interactions_view.columns:
                df_daily = df_interactions_view.groupby(df_interactions_view["timestamp"].dt.date).size().reset_index(name="consultas")
                fig, ax = plt.subplots(figsize=(7, 3.5))
                ax.plot(df_daily["timestamp"], df_daily["consultas"], marker="o", color="#3d405b")
                ax.set_title("Tendencia temporal de interacciones")
                ax.set_ylabel("Consultas")
                ax.set_xlabel("Fecha")
                plt.xticks(rotation=30, ha="right")
                st.pyplot(fig)
            else:
                st.info("No hay fechas suficientes para mostrar la tendencia temporal.")

    with tab_quant:
        st.subheader("Métricas cuantitativas")
        quant_choice = st.selectbox(
            "Selecciona la vista cuantitativa",
            ["Tiempo de respuesta", "Volumen por día", "Fuentes de respuesta", "Actividad por usuario", "Recursos del sistema"]
        )

        if quant_choice == "Tiempo de respuesta":
            if not df_interactions_view.empty and "response_time_s" in df_interactions_view.columns and not df_interactions_view["response_time_s"].dropna().empty:
                response_series = df_interactions_view["response_time_s"].dropna()
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
                ax1.hist(response_series, bins=min(12, max(5, len(response_series))), color="#3d405b", alpha=0.85)
                ax1.set_title("Histograma de tiempos")
                ax1.set_xlabel("Segundos")
                ax1.set_ylabel("Frecuencia")
                ax2.boxplot(response_series, vert=True)
                ax2.set_title("Boxplot de tiempos")
                ax2.set_ylabel("Segundos")
                st.pyplot(fig)

                df_stats = pd.DataFrame([{
                    "media": round(response_series.mean(), 2),
                    "mediana": round(response_series.median(), 2),
                    "mínimo": round(response_series.min(), 2),
                    "máximo": round(response_series.max(), 2),
                    "desv_std": round(response_series.std(ddof=0), 2)
                }])
                st.dataframe(df_stats, use_container_width=True)
                st.markdown("**Fórmula:** tiempo promedio = `Σ tiempo_respuesta / n`.")
            else:
                st.info("No hay tiempos de respuesta suficientes con los filtros actuales.")

        elif quant_choice == "Volumen por día":
            if not df_interactions_view.empty and "timestamp" in df_interactions_view.columns:
                df_daily = df_interactions_view.groupby(df_interactions_view["timestamp"].dt.date).size().reset_index(name="consultas")
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(df_daily["timestamp"].astype(str), df_daily["consultas"], color="#81b29a")
                ax.set_title("Consultas por día")
                ax.set_ylabel("Número de interacciones")
                plt.xticks(rotation=35, ha="right")
                st.pyplot(fig)
                st.dataframe(df_daily, use_container_width=True)
                st.markdown("**Método:** conteo de frecuencias por fecha para observar estacionalidad y picos de uso.")
            else:
                st.info("No hay datos temporales suficientes para esta vista.")

        elif quant_choice == "Fuentes de respuesta":
            if not source_counts.empty:
                df_sources = source_counts.reset_index()
                df_sources.columns = ["fuente", "interacciones"]
                df_sources["porcentaje"] = (df_sources["interacciones"] / max(1, df_sources["interacciones"].sum()) * 100).round(2)
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(df_sources["fuente"], df_sources["interacciones"], color="#e07a5f")
                ax.set_title("Composición por fuente")
                ax.set_ylabel("Interacciones")
                plt.xticks(rotation=25, ha="right")
                st.pyplot(fig)
                st.dataframe(df_sources, use_container_width=True)
                st.markdown("**Fórmula:** tasa por fuente = `(interacciones_fuente / interacciones_totales) * 100`.")
            else:
                st.info("No hay datos suficientes para mostrar la composición por fuente.")

        elif quant_choice == "Actividad por usuario":
            if not df_user_summary.empty:
                top_users = df_user_summary.head(10)
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.bar(top_users["user_id"], top_users["consultas_en_vista"], color="#3d405b")
                ax.set_title("Usuarios con mayor actividad")
                ax.set_ylabel("Consultas en vista")
                plt.xticks(rotation=35, ha="right")
                st.pyplot(fig)
                st.dataframe(df_user_summary, use_container_width=True)
            else:
                st.info("No hay usuarios suficientes para construir el ranking.")

        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("CPU (%)", round(quant.get("cpu_usage_percent", 0), 1))
            col2.metric("Memoria (%)", round(quant.get("memory_usage_percent", 0), 1))
            col3.metric("Errores", int(quant.get("errors_total", 0)))
            col4.metric("Alucinaciones", int(quant.get("hallucinations_total", 0)))

            st.markdown("### Telemetría de tokens")
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Tokens totales", int(quant.get("tokens_total", 0) or 0))
            t2.metric("Avg prompt tokens", float(quant.get("avg_prompt_tokens", 0) or 0))
            t3.metric("Avg completion tokens", float(quant.get("avg_completion_tokens", 0) or 0))
            t4.metric("Avg total tokens", float(quant.get("avg_total_tokens", 0) or 0))

            st.markdown("**Método:** observabilidad operativa usando métricas del proceso, sistema y consumo aproximado de tokens.")

    with tab_qual:
        st.subheader("Métricas cualitativas")
        qual_choice = st.selectbox(
            "Selecciona la vista cualitativa",
            ["Satisfacción", "Claridad", "Completitud", "Errores reportados", "Comentarios recientes"]
        )

        if df_feedbacks_view.empty:
            st.info("No hay feedback disponible con los filtros actuales.")
        elif qual_choice in ["Satisfacción", "Claridad", "Completitud"]:
            metric_map = {
                "Satisfacción": "satisfaction",
                "Claridad": "clarity",
                "Completitud": "completeness"
            }
            column = metric_map[qual_choice]
            series = df_feedbacks_view[column].dropna()
            if not series.empty:
                counts = series.value_counts().sort_index()
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(counts.index.astype(str), counts.values, color="#81b29a")
                ax.set_title(f"Distribución de {qual_choice.lower()}")
                ax.set_xlabel("Puntaje")
                ax.set_ylabel("Frecuencia")
                st.pyplot(fig)

                df_stats = pd.DataFrame([{
                    "media": round(series.mean(), 2),
                    "mediana": round(series.median(), 2),
                    "mínimo": round(series.min(), 2),
                    "máximo": round(series.max(), 2),
                    "desv_std": round(series.std(ddof=0), 2)
                }])
                st.dataframe(df_stats, use_container_width=True)
                st.markdown(f"**Fórmula:** promedio de {qual_choice.lower()} = `Σ puntuación / n`.")
                st.info(f"Interpretación: valores cercanos a 5 indican mejor percepción del usuario en el criterio de **{qual_choice.lower()}**.")
            else:
                st.info("No hay puntajes válidos para esta métrica en la vista actual.")

        elif qual_choice == "Errores reportados":
            df_errors = df_feedbacks_view[df_feedbacks_view["error_type"].astype(str).str.strip() != ""] if "error_type" in df_feedbacks_view.columns else pd.DataFrame()
            if not df_errors.empty:
                error_counts = df_errors["error_type"].value_counts().reset_index()
                error_counts.columns = ["tipo_error", "frecuencia"]
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(error_counts["tipo_error"], error_counts["frecuencia"], color="#e07a5f")
                ax.set_title("Errores reportados por tipo")
                ax.set_ylabel("Frecuencia")
                plt.xticks(rotation=30, ha="right")
                st.pyplot(fig)
                st.dataframe(error_counts, use_container_width=True)
            else:
                st.info("No hay errores reportados en el subconjunto actual.")

        else:
            comment_cols = [col for col in ["timestamp", "user_id", "question", "comments"] if col in df_feedbacks_view.columns]
            st.dataframe(df_feedbacks_view[comment_cols].tail(20), use_container_width=True)
            st.markdown("**Método:** análisis cualitativo manual de comentarios para detectar patrones y oportunidades de mejora.")

    with tab_users:
        st.subheader("Análisis por usuario")
        if df_user_summary.empty:
            st.info("No hay usuarios para mostrar con los filtros actuales.")
        else:
            st.markdown("### Ranking y comparación")
            st.dataframe(df_user_summary, use_container_width=True)
            download_dataframe(df_user_summary, "Descargar resumen por usuario", "resumen_usuarios_filtrado.csv")

            detail_user = st.selectbox("Selecciona un usuario para detalle", df_user_summary["user_id"].tolist())
            history_meta = history_summary.get(detail_user, {"conversations": 0, "historical_questions": 0, "active_chat": "-"})
            user_interactions = df_interactions_view[df_interactions_view["user_id"] == detail_user] if not df_interactions_view.empty else pd.DataFrame()
            user_feedback = df_feedbacks_view[df_feedbacks_view["user_id"] == detail_user] if not df_feedbacks_view.empty else pd.DataFrame()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Chats guardados", history_meta.get("conversations", 0))
            col2.metric("Preguntas históricas", history_meta.get("historical_questions", 0))
            col3.metric("Consultas en vista", len(user_interactions))
            col4.metric("Feedbacks", len(user_feedback))
            st.caption(f"Chat activo o más reciente: {history_meta.get('active_chat', '-')}")

            col1, col2 = st.columns(2)
            with col1:
                if not user_interactions.empty and "source" in user_interactions.columns:
                    source_counts_user = user_interactions["source"].value_counts()
                    fig, ax = plt.subplots(figsize=(7, 3.5))
                    ax.bar(source_counts_user.index.astype(str), source_counts_user.values, color="#3d405b")
                    ax.set_title(f"Fuentes de respuesta - {detail_user}")
                    ax.set_ylabel("Interacciones")
                    plt.xticks(rotation=25, ha="right")
                    st.pyplot(fig)
                else:
                    st.info("Sin datos de fuente para este usuario con los filtros actuales.")

            with col2:
                if not user_interactions.empty and "categories_list" in user_interactions.columns:
                    category_counts = user_interactions.explode("categories_list")["categories_list"].dropna().value_counts()
                    if not category_counts.empty:
                        fig, ax = plt.subplots(figsize=(7, 3.5))
                        ax.bar(category_counts.index.astype(str), category_counts.values, color="#81b29a")
                        ax.set_title(f"Categorías dominantes - {detail_user}")
                        ax.set_ylabel("Interacciones")
                        plt.xticks(rotation=25, ha="right")
                        st.pyplot(fig)
                    else:
                        st.info("Sin categorías suficientes para este usuario.")
                else:
                    st.info("No hay categorías disponibles para este usuario.")

            history_rows = []
            for conv in user_histories.get(detail_user, {}).get("conversations", []):
                for message in conv.get("messages", []):
                    if isinstance(message, (list, tuple)) and len(message) >= 2:
                        history_rows.append({
                            "chat": conv.get("title", "-"),
                            "pregunta": message[0],
                            "respuesta": str(message[1])[:180],
                            "tiempo_s": message[2] if len(message) > 2 else "",
                            "timestamp": message[3] if len(message) > 3 else ""
                        })

            if history_rows:
                df_history = pd.DataFrame(history_rows[-20:])
                st.markdown("### Historial reciente")
                st.dataframe(df_history, use_container_width=True)
                download_dataframe(df_history, f"Descargar historial de {detail_user}", f"historial_{detail_user}.csv")

            if not user_feedback.empty:
                st.markdown("### Feedback del usuario")
                cols = [col for col in ["timestamp", "question", "satisfaction", "clarity", "completeness", "error_type", "comments"] if col in user_feedback.columns]
                st.dataframe(user_feedback[cols].tail(15), use_container_width=True)

    with tab_routing:
        st.subheader("Observabilidad de Routing y GRAPH_RAG")

        if df_interactions_view.empty:
            st.info("No hay interacciones para analizar routing con los filtros actuales.")
        else:
            if "source" in df_interactions_view.columns:
                source_series_rt = df_interactions_view["source"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
                source_counts_rt = source_series_rt.value_counts()
                total_rt = int(source_counts_rt.sum())
                graph_rt = int(source_counts_rt.get("GRAPH_RAG", 0))
                graph_pct = round((graph_rt / total_rt) * 100, 2) if total_rt else 0.0

                c1, c2, c3 = st.columns(3)
                c1.metric("Interacciones analizadas", total_rt)
                c2.metric("GRAPH_RAG", graph_rt)
                c3.metric("% GRAPH_RAG", f"{graph_pct}%")

                fig, ax = plt.subplots(figsize=(8, 3.8))
                ax.bar(source_counts_rt.index.astype(str), source_counts_rt.values, color="#6d597a")
                ax.set_title("Distribución de modos de respuesta")
                ax.set_ylabel("Interacciones")
                plt.xticks(rotation=25, ha="right")
                st.pyplot(fig)

                df_src = source_counts_rt.reset_index()
                df_src.columns = ["source", "count"]
                df_src["percent"] = (df_src["count"] / max(1, df_src["count"].sum()) * 100).round(2)
                st.dataframe(df_src, use_container_width=True)
            else:
                st.warning("La columna 'source' no está disponible en las interacciones filtradas.")

            trace_cols = [c for c in ["timestamp", "user_id", "question", "source", "confidence", "routing_trace", "timing_ms"] if c in df_interactions_view.columns]
            if trace_cols:
                trace_df = df_interactions_view[trace_cols].sort_values("timestamp", ascending=False).head(30) if "timestamp" in df_interactions_view.columns else df_interactions_view[trace_cols].head(30)
                st.markdown("### Trazas recientes")
                st.dataframe(trace_df, use_container_width=True)
                download_dataframe(trace_df, "Descargar trazas recientes", "routing_traces_recientes.csv")

            if "routing_trace" in df_interactions_view.columns:
                reasons = []
                for trace in df_interactions_view["routing_trace"].tolist():
                    if isinstance(trace, dict):
                        reason = str(trace.get("decision_reason", "")).strip()
                        if reason:
                            reasons.append(reason)
                if reasons:
                    df_reasons = pd.Series(reasons).value_counts().reset_index()
                    df_reasons.columns = ["decision_reason", "count"]
                    st.markdown("### Razones de enrutamiento")
                    st.dataframe(df_reasons, use_container_width=True)

    with tab_method:
        st.subheader("Metodología, fórmulas y criterios")
        st.markdown("""
        ### Fuentes de datos utilizadas
        - `interaction_logs.jsonl`: registro central de interacciones del chatbot.
        - `feedback.jsonl`: evaluación cualitativa realizada por usuarios.
        - `user_histories.json`: histórico de conversaciones por usuario para análisis longitudinal.

        ### Métodos empleados
        - **Estadística descriptiva:** media, mediana, desviación estándar, máximos y mínimos.
        - **Análisis de frecuencia:** conteos por usuario, categoría y fuente de respuesta.
        - **Segmentación por filtros:** fecha, usuario, fuente, categoría y presencia de feedback.
        - **Análisis comparativo:** contraste entre consultas visibles y consultas históricas acumuladas.
        """)

        formula_df = pd.DataFrame([
            {"Indicador": "Tiempo promedio de respuesta", "Fórmula": "Σ tiempo_respuesta / n", "Interpretación": "Menor valor implica mayor eficiencia"},
            {"Indicador": "Tasa de caché", "Fórmula": "(cache_hits / interacciones_totales) * 100", "Interpretación": "Mide automatización y rapidez"},
            {"Indicador": "Promedio de satisfacción", "Fórmula": "Σ satisfaction / n", "Interpretación": "Mayor valor implica mejor percepción"},
            {"Indicador": "Promedio de claridad", "Fórmula": "Σ clarity / n", "Interpretación": "Mide comprensión de las respuestas"},
            {"Indicador": "Promedio de completitud", "Fórmula": "Σ completeness / n", "Interpretación": "Mide cobertura de la respuesta"},
            {"Indicador": "Tasa de alucinación", "Fórmula": "(hallucinations / interacciones_totales) * 100", "Interpretación": "Menor valor implica mayor confiabilidad"}
        ])
        st.dataframe(formula_df, use_container_width=True)

        st.latex(r"\bar{x} = \frac{\sum_{i=1}^{n} x_i}{n}")
        st.latex(r"\text{Tasa} = \frac{\text{casos de interés}}{\text{total de observaciones}} \times 100")

    with tab_ragas:
        st.subheader("Resultados de evaluación RAGAS")
        ragas_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evaluation", "results")
        ragas_file = os.path.join(ragas_path, "eval_results_v1_streaming.json")
        if os.path.exists(ragas_file):
            try:
                with open(ragas_file, "r", encoding="utf-8") as f:
                    ragas_data = json.load(f)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Faithfulness", round(float(ragas_data.get("avg_faithfulness", 0) or 0), 3))
                c2.metric("Context Precision", round(float(ragas_data.get("avg_context_precision", 0) or 0), 3))
                c3.metric("Context Recall", round(float(ragas_data.get("avg_context_recall", 0) or 0), 3))
                c4.metric("Answer Relevancy", round(float(ragas_data.get("avg_answer_relevancy", 0) or 0), 3))

                st.markdown("### Resumen de corrida")
                st.json({
                    "timestamp": ragas_data.get("timestamp"),
                    "total_cases": ragas_data.get("total_cases"),
                    "successful": ragas_data.get("successful"),
                    "failed": ragas_data.get("failed"),
                    "overall_type_accuracy": ragas_data.get("overall_type_accuracy"),
                })

                results = ragas_data.get("results", [])
                if results:
                    df_ragas = pd.DataFrame(results)
                    cols = [c for c in ["question", "expected_type", "actual_type_canonical", "faithfulness", "context_precision", "context_recall", "answer_relevancy", "success"] if c in df_ragas.columns]
                    st.dataframe(df_ragas[cols], use_container_width=True)
                    download_dataframe(df_ragas[cols], "Descargar resultados RAGAS", "ragas_results_filtered.csv")
            except Exception as e:
                st.warning(f"No se pudo leer resultados RAGAS: {e}")
        else:
            st.info("No se encontró archivo de resultados RAGAS en evaluation/results/eval_results_v1_streaming.json")

    with tab_data:
        st.subheader("Datos filtrados y exportes")
        with st.expander("Interacciones filtradas", expanded=True):
            if not df_interactions_view.empty:
                interaction_cols = [col for col in ["timestamp", "user_id", "source", "category_label", "question", "response_time_s", "hallucinated", "response_preview"] if col in df_interactions_view.columns]
                st.dataframe(df_interactions_view[interaction_cols].sort_values("timestamp", ascending=False), use_container_width=True)
                download_dataframe(df_interactions_view[interaction_cols], "Descargar interacciones filtradas", "interacciones_filtradas.csv")
            else:
                st.info("No hay interacciones con los filtros actuales.")

        with st.expander("Feedback filtrado", expanded=False):
            if not df_feedbacks_view.empty:
                feedback_cols = [col for col in ["timestamp", "user_id", "question", "satisfaction", "clarity", "completeness", "error_type", "comments"] if col in df_feedbacks_view.columns]
                st.dataframe(df_feedbacks_view[feedback_cols].sort_values("timestamp", ascending=False), use_container_width=True)
                download_dataframe(df_feedbacks_view[feedback_cols], "Descargar feedback filtrado", "feedback_filtrado.csv")
            else:
                st.info("No hay feedback con los filtros actuales.")

        with st.expander("Resumen narrativo para tesis", expanded=False):
            st.markdown(f"""
            **Interpretación sugerida:** en el periodo filtrado se registraron **{view_total_queries} interacciones** correspondientes a **{visible_users} usuarios**. 
            La fuente dominante fue **{top_source}**, mientras que el promedio de satisfacción alcanzó **{avg_satisfaction}/5** y la claridad **{avg_clarity}/5**. 
            Estos resultados permiten describir el desempeño del asistente desde una perspectiva cuantitativa y cualitativa, apoyando el análisis experimental de la tesis.
            """)

    st.write("---")
    st.write(f"**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if st.button("🔄 Actualizar Ahora"):
        st.rerun()

else:
    st.error("❌ No se pudieron obtener las métricas. Verifica que:")
    st.write("1. El servidor FastAPI esté corriendo (`python mcp_server_local.py`)")
    st.write("2. Ollama esté activo (`ollama serve`)")
    st.write("3. Redis esté corriendo (`redis-server`)")
    st.write("4. Se hayan hecho al menos algunas consultas desde el cliente principal")
