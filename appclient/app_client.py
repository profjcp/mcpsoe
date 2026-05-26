import streamlit as st
import streamlit.components.v1 as components
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
                                "http://127.0.0.1:9000/ask_cliente",
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

        /* ── Avatar de usuario ── */
        .user-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f2a65a, #d97745);
            color: #1d2735;
            font-weight: 700;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 8px auto;
        }
        .user-info-block {
            text-align: center;
            margin-bottom: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .user-info-block .uname {
            color: #eef3fa;
            font-weight: 700;
            font-size: 15px;
        }
        .user-info-block .urole {
            color: #a0b0c5;
            font-size: 12px;
            margin-top: 2px;
        }

        /* ── Panel de login ── */
        .login-wrap  { max-width: 420px; margin: 40px auto; }
        .login-header { text-align: center; padding: 10px 0 20px 0; }
        .login-icon  { font-size: 40px; display: block; margin-bottom: 6px; }
        .login-title { font-size: 22px; font-weight: 700; color: var(--ink); }
        .login-sub   { color: var(--muted); font-size: 14px; margin-top: 4px; }

        /* ── Fila de feedback ── */
        .fb-row { display: flex; gap: 6px; margin: 2px 0 8px 0; align-items: center; }

        /* ── Animación de burbujas ── */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ── Botones de historial estilo card ── */
        .hist-card-wrap { margin: 4px 0; }

        .hist-card-wrap [data-testid="stButton"] > button {
            background: rgba(255,255,255,0.06) !important;
            color: #dce8f5 !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 10px !important;
            padding: 10px 13px !important;
            text-align: left !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            line-height: 1.4 !important;
            cursor: pointer !important;
            transition: background 0.14s, border-color 0.14s !important;
            box-shadow: none !important;
            transform: none !important;
            width: 100% !important;
        }

        .hist-card-wrap [data-testid="stButton"] > button:hover {
            background: rgba(255,255,255,0.13) !important;
            border-color: rgba(255,255,255,0.28) !important;
            color: #ffffff !important;
        }

        .hist-active [data-testid="stButton"] > button {
            background: rgba(242,166,90,0.18) !important;
            border-left: 3px solid #f2a65a !important;
            color: #ffdeb8 !important;
        }

        .hist-active [data-testid="stButton"] > button:hover {
            background: rgba(242,166,90,0.26) !important;
        }

        /* meta caption debajo del botón-card */
        .hist-card-wrap [data-testid="stCaptionContainer"] p {
            color: #8aa3bf !important;
            font-size: 11px !important;
            margin: -6px 0 6px 13px !important;
            padding: 0 !important;
        }

        /* ── Responsive ── */
        @media (max-width: 768px) {
            .panel  { padding: 10px; border-radius: 10px; }
            .bubble { padding: 10px 11px; }
            .app-title { font-size: 22px; }
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

def render_message(role, text, response_time=None, timestamp=None):
    css_class = "user" if role == "user" else "bot"
    if role == "user":
        safe_text = safe_html_text(text).replace("\n", "<br>")
        st.markdown(f"<div class='bubble {css_class}'>{safe_text}</div>", unsafe_allow_html=True)
    else:
        # Bot: preservar negrita e itálica del markdown
        escaped = safe_html_text(text)
        escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
        escaped = re.sub(r'\*(.*?)\*', r'<em>\1</em>', escaped)
        escaped = escaped.replace('\n', '<br>')
        st.markdown(f"<div class='bubble {css_class}'>{escaped}</div>", unsafe_allow_html=True)
        parts = []
        if response_time is not None:
            parts.append(f"⏱ {response_time:.2f}s")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                parts.append(dt.strftime("%H:%M"))
            except Exception:
                pass
        meta_str = " · ".join(parts) if parts else "N/A"
        st.markdown(f"<div class='meta'>{meta_str}</div>", unsafe_allow_html=True)

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
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='login-header'>"
        "<span class='login-icon'>🎓</span>"
        "<div class='login-title'>SoeBOT — UAGRM/SOE</div>"
        "<div class='login-sub'>Asistente académico con FAQs y RAG</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    tab_login, tab_reg = st.tabs(["Iniciar Sesión", "Registrarse"])

    with tab_login:
        username_l = st.text_input("Usuario:", key="login_user")
        password_l = st.text_input("Contraseña:", type="password", key="login_pass")
        if st.button("Iniciar Sesión", use_container_width=True, key="btn_login"):
            if username_l in users and users[username_l] == password_l:
                st.session_state.logged_in = True
                st.session_state.user_id = username_l
                normalized = normalize_user_history(user_histories.get(username_l, []))
                st.session_state.conversations = normalized["conversations"]
                st.session_state.active_conversation_id = normalized.get("active_id")
                st.success(f"Bienvenido, {username_l}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with tab_reg:
        username_r = st.text_input("Nuevo usuario:", key="reg_user")
        password_r = st.text_input("Contraseña:", type="password", key="reg_pass")
        if st.button("Registrarse", use_container_width=True, key="btn_reg"):
            if username_r and password_r:
                if not USERNAME_PATTERN.match(username_r):
                    st.error("Usuario inválido. Usa 3-30 caracteres: letras, números, _, - o .")
                    st.stop()
                if username_r in users:
                    st.error("El usuario ya existe. Elige otro nombre.")
                else:
                    users[username_r] = password_r
                    save_users(users)
                    user_histories[username_r] = {"conversations": [], "active_id": None}
                    save_histories(user_histories)
                    st.success(f"Usuario {username_r} registrado exitosamente. Ahora puedes iniciar sesión.")
            else:
                st.error("Por favor, ingresa un usuario y contraseña válidos.")

    st.markdown("</div>", unsafe_allow_html=True)
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
        # Avatar con iniciales
        initial = st.session_state.user_id[0].upper() if st.session_state.user_id else "?"
        st.markdown(
            f"<div class='user-info-block'>"
            f"<div class='user-avatar'>{initial}</div>"
            f"<div class='uname'>{safe_html_text(st.session_state.user_id)}</div>"
            f"<div class='urole'>Estudiante SOE</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        new_chat_clicked = st.button("Nuevo chat", key="new_chat_btn", use_container_width=True)

        if st.session_state.conversations:
            for conv in reversed(st.session_state.conversations):
                is_active = conv["id"] == st.session_state.active_conversation_id
                title = conv["title"]
                count = len(conv.get("messages", []))
                preview = get_conversation_preview(conv)
                # Timestamp del último mensaje
                last_ts = ""
                _msgs = conv.get("messages", [])
                if _msgs:
                    _last = _msgs[-1]
                    if isinstance(_last, (list, tuple)) and len(_last) >= 4:
                        try:
                            last_ts = datetime.fromisoformat(_last[3]).strftime("%d/%m %H:%M")
                        except Exception:
                            pass

                active_cls = "hist-active" if is_active else ""
                st.markdown(f'<div class="hist-card-wrap {active_cls}">', unsafe_allow_html=True)
                if st.button(title, key=f"open_{conv['id']}", use_container_width=True):
                    if not is_active:
                        st.session_state.active_conversation_id = conv["id"]
                        save_user_state(
                            st.session_state.user_id,
                            st.session_state.conversations,
                            st.session_state.active_conversation_id
                        )
                        st.rerun()
                meta_parts = [f"{count} msg"]
                if last_ts:
                    meta_parts.append(last_ts)
                if preview and preview != "Sin mensajes todavía.":
                    meta_parts.append(preview[:45])
                st.caption(" · ".join(meta_parts))
                st.markdown('</div>', unsafe_allow_html=True)

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
                ts = item[3] if len(item) >= 4 else None
                render_message("user", q)
                render_message("bot", a, t, ts)

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

    # Scroll automático al último mensaje
    components.html(
        "<script>"
        "var m=window.parent.document.querySelectorAll('[data-testid=stMain],[data-testid=stAppViewBlockContainer]');"
        "m.forEach(function(el){el.scrollTo(0,el.scrollHeight);});"
        "</script>",
        height=0,
    )

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

<<<<<<< HEAD
    st.markdown("</div>", unsafe_allow_html=True)
=======
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
                        "http://127.0.0.1:9000/ask_cliente",
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
>>>>>>> b12bd27f
