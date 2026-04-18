import streamlit as st
import requests
import time
import json
import os
import html
import re
from datetime import datetime

st.set_page_config(page_title="SoeBOT WebUI", page_icon="🤖", layout="wide")

def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

        :root {
            --bg-1: #f6f4ef;
            --bg-2: #ebe5d9;
            --ink: #17212f;
            --panel: #fffdfa;
            --panel-strong: #f2ecdf;
            --accent: #d97745;
            --accent-2: #28405c;
            --muted: #5c6675;
        }

        .stApp {
            background: radial-gradient(1200px 600px at 10% -10%, var(--bg-2) 0%, var(--bg-1) 45%, #fefefe 100%);
            color: var(--ink);
            font-family: 'Space Grotesk', sans-serif;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #223349 0%, #1b2a3f 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        section[data-testid="stSidebar"] * {
            color: #eef3fa;
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
        section[data-testid="stSidebar"] .stCaption {
            color: #eef3fa !important;
        }

        section[data-testid="stSidebar"] .stButton>button {
            background: #f2a65a;
            color: #1d2735;
            font-weight: 700;
            border: none;
        }

        section[data-testid="stSidebar"] .stButton>button:hover {
            background: #f09a45;
        }

        section[data-testid="stSidebar"] .stAlert {
            background: rgba(255, 255, 255, 0.08);
            color: #f2f6fb;
            border: 1px solid rgba(255, 255, 255, 0.12);
        }

        .app-title {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 0.2px;
            margin: 0 0 12px 0;
        }

        .app-subtitle {
            color: var(--muted);
            margin: 0 0 18px 0;
        }

        .panel {
            background: var(--panel);
            border: 1px solid #e3d8c7;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 8px 24px rgba(19, 35, 58, 0.08);
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .panel-title {
            font-weight: 700;
        }

        .badge {
            font-family: 'IBM Plex Mono', monospace;
            background: #ece6dc;
            border: 1px solid #d8cbba;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 12px;
            color: #2a3d56;
        }

        .bubble {
            padding: 12px 14px;
            border-radius: 14px;
            margin: 10px 0;
            line-height: 1.45;
            border: 1px solid #e2d8c8;
            color: #1b2736;
        }

        .bubble.user {
            background: #fff3e5;
            border-left: 4px solid var(--accent);
        }

        .bubble.bot {
            background: #ffffff;
            border-left: 4px solid var(--accent-2);
        }

        .meta {
            color: var(--muted);
            font-size: 12px;
            margin-top: 4px;
        }

        .stButton>button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 10px;
            font-weight: 600;
        }

        .stButton>button:hover {
            background: #c9683e;
        }

        .stTextInput>div>div>input,
        .stTextArea textarea,
        .stSelectbox>div>div,
        .stNumberInput input {
            background: #fffefa !important;
            color: #1b2736 !important;
            border: 1px solid #d9cdb9 !important;
            border-radius: 10px;
        }

        .stTextInput>div>div>input::placeholder,
        .stTextArea textarea::placeholder {
            color: #7a8698;
        }

        [data-baseweb="select"] > div {
            background: #fffefa !important;
            color: #1b2736 !important;
            border: 1px solid #d9cdb9 !important;
        }

        .stSlider [data-baseweb="slider"] {
            margin-top: 8px;
        }

        .history-card {
            background: #fffdf8;
            border: 1px solid #e2d8c8;
            border-radius: 12px;
            padding: 10px 12px;
            margin: 8px 0 6px 0;
            color: #1f2937;
        }

        .history-card.active {
            border-left: 4px solid var(--accent);
            background: #fff1e3;
        }

        .history-title {
            font-weight: 700;
            margin-bottom: 4px;
            color: #111827;
        }

        .history-preview {
            color: #4b5563;
            font-size: 13px;
            line-height: 1.35;
        }

        .history-meta {
            color: #6b7280;
            font-size: 12px;
            margin-bottom: 4px;
        }

        section[data-testid="stSidebar"] .history-card,
        section[data-testid="stSidebar"] .history-card * {
            color: #1f2937 !important;
        }

        .helper-box {
            background: #f7f2e8;
            border: 1px dashed #cfae8b;
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 14px;
            color: var(--accent-2);
            line-height: 1.45;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_styles()

st.markdown("<div class='app-title'>SoeBOT</div>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>Chat academico con FAQs por dominio y RAG</div>", unsafe_allow_html=True)

# Archivos para persistir datos
HISTORIES_FILE = "user_histories.json"
USERS_FILE = "users.json"

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")

def safe_html_text(value):
    return html.escape(str(value), quote=True)

# Función para cargar históricos desde archivo
def load_histories():
    if os.path.exists(HISTORIES_FILE):
        with open(HISTORIES_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Función para guardar históricos en archivo
def save_histories(histories):
    with open(HISTORIES_FILE, "w") as f:
        json.dump(histories, f, indent=4)

# Función para cargar usuarios desde archivo
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Función para guardar usuarios en archivo
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def normalize_user_history(raw_history):
    if isinstance(raw_history, dict) and "conversations" in raw_history:
        return raw_history
    if isinstance(raw_history, list):
        return {
            "conversations": [
                {
                    "id": "chat_1",
                    "title": "Chat 1",
                    "messages": raw_history
                }
            ],
            "active_id": "chat_1"
        }
    return {
        "conversations": [],
        "active_id": None
    }

def save_user_state(user_id, conversations, active_id):
    user_histories[user_id] = {
        "conversations": conversations,
        "active_id": active_id
    }
    save_histories(user_histories)

def get_active_conversation(conversations, active_id):
    for conv in conversations:
        if conv["id"] == active_id:
            return conv
    return conversations[0] if conversations else None

def get_conversation_preview(conversation, max_len=80):
    messages = conversation.get("messages", [])
    if not messages:
        return "Sin mensajes todavía."

    latest = messages[-1]
    latest_question = latest[0] if isinstance(latest, (list, tuple)) and len(latest) > 0 else ""
    preview = str(latest_question).replace("\n", " ").strip()
    return preview[:max_len] + ("..." if len(preview) > max_len else "")

def render_message(role, text, response_time=None):
    safe_text = safe_html_text(text).replace("\n", "<br>")
    css_class = "user" if role == "user" else "bot"
    st.markdown(f"<div class='bubble {css_class}'>{safe_text}</div>", unsafe_allow_html=True)
    if role == "bot":
        if response_time is None:
            st.markdown("<div class='meta'>Tiempo de respuesta: N/A</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='meta'>Tiempo de respuesta: {response_time:.2f} segundos</div>", unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("### Panel rapido")
        if st.session_state.get("logged_in") and st.session_state.get("user_id"):
            st.success(f"Sesion iniciada: {st.session_state.user_id}")
            st.caption("Tip: usa preguntas concretas para respuestas mas precisas.")
        else:
            st.info("Inicia sesion para acceder a tus chats e historial.")

        st.markdown("---")
        st.markdown("**Consultas sugeridas**")
        st.markdown("- Moodle y tareas")
        st.markdown("- Horarios y programas")
        st.markdown("- Tutor y monografia")

        st.markdown("---")
        st.caption("SoeBOT | FAQ + RAG")

# Cargar datos globales
user_histories = load_histories()
users = load_users()

# Estado de sesión
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None

# Pantalla de Login/Registro
if not st.session_state.logged_in:
    render_sidebar()
    st.subheader("Acceso a SoeBOT")
    action = st.radio("Selecciona una opción:", ("Iniciar Sesión", "Registrarse"))
    
    username = st.text_input("Usuario:")
    password = st.text_input("Contraseña:", type="password")
    
    if action == "Iniciar Sesión":
        if st.button("Iniciar Sesión"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.user_id = username
                normalized = normalize_user_history(user_histories.get(username, []))
                st.session_state.conversations = normalized["conversations"]
                st.session_state.active_conversation_id = normalized.get("active_id")
                st.success(f"Bienvenido, {username}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    elif action == "Registrarse":
        if st.button("Registrarse"):
            if username and password:
                if not USERNAME_PATTERN.match(username):
                    st.error("Usuario inválido. Usa 3-30 caracteres: letras, números, _, - o .")
                    st.stop()
                if username in users:
                    st.error("El usuario ya existe. Elige otro nombre.")
                else:
                    users[username] = password
                    save_users(users)
                    user_histories[username] = {"conversations": [], "active_id": None}
                    save_histories(user_histories)
                    st.success(f"Usuario {username} registrado exitosamente. Ahora puedes iniciar sesión.")
            else:
                st.error("Por favor, ingresa un usuario y contraseña válidos.")
else:
    if st.session_state.user_id and st.session_state.user_id in user_histories and not st.session_state.conversations:
        normalized = normalize_user_history(user_histories.get(st.session_state.user_id, []))
        st.session_state.conversations = normalized["conversations"]
        if not st.session_state.active_conversation_id:
            st.session_state.active_conversation_id = normalized.get("active_id")

    if not st.session_state.conversations:
        st.session_state.conversations = []

    if st.session_state.active_conversation_id is None:
        new_id = f"chat_{int(time.time())}"
        st.session_state.conversations.append({"id": new_id, "title": "Chat 1", "messages": []})
        st.session_state.active_conversation_id = new_id

    with st.sidebar:
        st.markdown("### Historial")
        st.caption("Todos tus chats quedan en esta barra lateral.")

        new_chat_clicked = st.button("Nuevo chat", key="new_chat_btn", use_container_width=True)

        if st.session_state.conversations:
            for conv in reversed(st.session_state.conversations):
                is_active = conv["id"] == st.session_state.active_conversation_id
                card_class = "history-card active" if is_active else "history-card"
                preview = safe_html_text(get_conversation_preview(conv))
                title = safe_html_text(conv["title"])
                count = len(conv.get("messages", []))

                st.markdown(
                    f"""
                    <div class='{card_class}'>
                        <div class='history-title'>{title}</div>
                        <div class='history-meta'>{count} mensaje(s)</div>
                        <div class='history-preview'>{preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    "Abrir este chat" if not is_active else "Chat actual",
                    key=f"open_{conv['id']}",
                    use_container_width=True,
                    disabled=is_active
                ):
                    st.session_state.active_conversation_id = conv["id"]
                    save_user_state(
                        st.session_state.user_id,
                        st.session_state.conversations,
                        st.session_state.active_conversation_id
                    )
                    st.rerun()

        st.markdown("---")
        st.markdown("**Consultas sugeridas**")
        st.markdown("- Moodle y tareas")
        st.markdown("- Horarios y programas")
        st.markdown("- Tutor y monografia")

        if new_chat_clicked:
            new_id = f"chat_{int(time.time())}"
            st.session_state.conversations.append({"id": new_id, "title": f"Chat {len(st.session_state.conversations) + 1}", "messages": []})
            st.session_state.active_conversation_id = new_id
            save_user_state(
                st.session_state.user_id,
                st.session_state.conversations,
                st.session_state.active_conversation_id
            )
            st.rerun()

        if st.button("Cerrar Sesion", use_container_width=True):
            save_user_state(
                st.session_state.user_id,
                st.session_state.conversations,
                st.session_state.active_conversation_id
            )
            st.session_state.update({"logged_in": False, "user_id": None, "conversations": [], "active_conversation_id": None})
            st.rerun()

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    safe_user_id = safe_html_text(st.session_state.user_id)
    st.markdown(f"<div class='panel-header'><span class='panel-title'>Sesion de: {safe_user_id}</span><span class='badge'>Activo</span></div>", unsafe_allow_html=True)

    active_conversation = get_active_conversation(
        st.session_state.conversations,
        st.session_state.active_conversation_id
    )

    if active_conversation and not active_conversation.get("messages"):
        st.markdown(
            """
            <div class='helper-box'>
                <strong>Puedes preguntarme sobre:</strong> inscripciones, certificados, Moodle, programas, horarios, docentes, tutorías e investigación.<br><br>
                <strong>Ejemplos:</strong><br>
                • ¿Cómo puedo subir una tarea a Moodle?<br>
                • ¿Cuáles son los horarios de Ciberseguridad?<br>
                • ¿Cómo puedo obtener mi tutor?
            </div>
            """,
            unsafe_allow_html=True
        )

    if active_conversation:
        for idx, item in enumerate(active_conversation["messages"]):
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                q, a, t = item[0], item[1], item[2]
                render_message("user", q)
                render_message("bot", a, t)

                with st.expander("Enviar Feedback (opcional)"):
                    col1, col2, col3 = st.columns(3)
                    satisfaction = col1.slider("Satisfaccion", 1, 5, 3, key=f"sat_{idx}")
                    clarity = col2.slider("Claridad", 1, 5, 3, key=f"clar_{idx}")
                    completeness = col3.slider("Completitud", 1, 5, 3, key=f"comp_{idx}")

                    error_type = st.selectbox(
                        "Hubo algun error?",
                        ["Ninguno", "Contexto insuficiente", "Alucinacion", "Interpretacion erronea", "Formato incorrecto"],
                        key=f"err_{idx}"
                    )
                    comments = st.text_area("Comentarios adicionales", key=f"comm_{idx}")

                    if st.button("Enviar Feedback", key=f"btn_{idx}"):
                        try:
                            error_val = "" if error_type == "Ninguno" else error_type
                            feedback_response = requests.post(
                                "http://127.0.0.1:9000/feedback",
                                json={
                                    "question": q,
                                    "response": a,
                                    "user_id": st.session_state.user_id,
                                    "satisfaction": satisfaction,
                                    "clarity": clarity,
                                    "completeness": completeness,
                                    "error_type": error_val,
                                    "comments": comments
                                }
                            )
                            if feedback_response.status_code == 200:
                                st.success("Feedback guardado. Gracias.")
                            else:
                                st.error("Error al enviar feedback.")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                q, a = item
                render_message("user", q)
                render_message("bot", a)

    question = st.text_input(
        "Escribe tu pregunta",
        key="input_box",
        placeholder="Ej.: ¿Cómo puedo subir una tarea a Moodle?"
    )

    if st.button("Enviar") and question.strip():
        answer_placeholder = st.empty()
        answer_wrapper = {"text": ""}

        if active_conversation and not active_conversation["messages"]:
            short_title = question.strip()[:36]
            active_conversation["title"] = short_title if len(short_title) > 0 else active_conversation["title"]

        try:
            with st.spinner("Consultando a la IA..."):
                start_time = time.time()
                print(f"--- CLIENTE: [{start_time}] Iniciando peticion para usuario {st.session_state.user_id}.")

                with requests.post(
                    "http://127.0.0.1:9000/ask",
                    json={"question": question, "user_id": st.session_state.user_id},
                    stream=True
                ) as response:
                    response.raise_for_status()
                    first_chunk = True
                    for chunk in response.iter_content(chunk_size=None):
                        if first_chunk:
                            first_chunk_time = time.time()
                            print(f"--- CLIENTE: [{first_chunk_time}] Primer chunk recibido en {first_chunk_time - start_time:.2f}s")
                            first_chunk = False
                        if chunk:
                            decoded_chunk = chunk.decode("utf-8")
                            answer_wrapper["text"] += decoded_chunk
                            answer_placeholder.markdown(
                                f"<div class='bubble bot'>{safe_html_text(answer_wrapper['text']).replace('\n', '<br>')}</div>",
                                unsafe_allow_html=True
                            )

            end_time = time.time()
            response_time = end_time - start_time
            st.markdown(f"<div class='meta'>Tiempo de respuesta: {response_time:.2f} segundos</div>", unsafe_allow_html=True)

            if active_conversation is None:
                new_id = f"chat_{int(time.time())}"
                active_conversation = {"id": new_id, "title": "Chat 1", "messages": []}
                st.session_state.conversations.append(active_conversation)
                st.session_state.active_conversation_id = new_id

            active_conversation["messages"].append((question, answer_wrapper["text"], response_time, datetime.now().isoformat()))
            save_user_state(
                st.session_state.user_id,
                st.session_state.conversations,
                st.session_state.active_conversation_id
            )
            st.rerun()

        except requests.exceptions.RequestException:
            st.error("Error de conexion: no se pudo conectar al servidor MCP.")
        except Exception as e:
            st.error(f"Ocurrio un error inesperado: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
