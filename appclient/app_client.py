import streamlit as st
import requests
import time
import json
import os
import html

st.set_page_config(page_title="SoeBOT WebUI", page_icon="🤖", layout="wide")

def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

        :root {
            --bg-1: #f7f1e8;
            --bg-2: #f0e0c3;
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
            border: 1px solid #ead7c0;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.05);
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
            background: #f2e9e4;
            border: 1px solid #e4cbb1;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 12px;
            color: var(--accent-2);
        }

        .bubble {
            padding: 12px 14px;
            border-radius: 14px;
            margin: 10px 0;
            line-height: 1.45;
            border: 1px solid #ead7c0;
        }

        .bubble.user {
            background: #fef6ed;
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
            background: #d46f55;
        }

        .stTextInput>div>div>input {
            border-radius: 10px;
        }

        .stSelectbox>div>div>div {
            border-radius: 10px;
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

def render_message(role, text, response_time=None):
    safe_text = html.escape(text).replace("\n", "<br>")
    css_class = "user" if role == "user" else "bot"
    st.markdown(f"<div class='bubble {css_class}'>{safe_text}</div>", unsafe_allow_html=True)
    if role == "bot":
        if response_time is None:
            st.markdown("<div class='meta'>Tiempo de respuesta: N/A</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='meta'>Tiempo de respuesta: {response_time:.2f} segundos</div>", unsafe_allow_html=True)

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
    # Pantalla principal con layout tipo Gemini
    left_col, right_col = st.columns([1, 3], gap="large")

    with left_col:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'><span class='panel-title'>Historial</span><span class='badge'>Chats</span></div>", unsafe_allow_html=True)

        new_chat_clicked = st.button("Nuevo chat", key="new_chat_btn")

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

        titles = [c["title"] for c in st.session_state.conversations]
        current_index = 0
        for idx, conv in enumerate(st.session_state.conversations):
            if conv["id"] == st.session_state.active_conversation_id:
                current_index = idx
                break

        if titles:
            selected_title = st.selectbox("Conversaciones", titles, index=current_index)
            selected_index = titles.index(selected_title)
            st.session_state.active_conversation_id = st.session_state.conversations[selected_index]["id"]

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

        if st.button("Cerrar Sesion"):
            save_user_state(
                st.session_state.user_id,
                st.session_state.conversations,
                st.session_state.active_conversation_id
            )
            st.session_state.update({"logged_in": False, "user_id": None, "conversations": [], "active_conversation_id": None})
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown(f"<div class='panel-header'><span class='panel-title'>Sesion de: {st.session_state.user_id}</span><span class='badge'>Activo</span></div>", unsafe_allow_html=True)

        active_conversation = get_active_conversation(
            st.session_state.conversations,
            st.session_state.active_conversation_id
        )

        if active_conversation:
            for idx, item in enumerate(active_conversation["messages"]):
                if len(item) == 3:
                    q, a, t = item
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

        question = st.text_input("Escribe tu pregunta", key="input_box")

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
                                    f"<div class='bubble bot'>{html.escape(answer_wrapper['text']).replace('\n', '<br>')}</div>",
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

                active_conversation["messages"].append((question, answer_wrapper["text"], response_time))
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
