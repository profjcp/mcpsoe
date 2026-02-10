import streamlit as st
import requests
import time
import json
import os

st.set_page_config(page_title="SoeBOT WebUI", page_icon="🤖")

st.title("SoeBOT - Chat con tu IA")

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

# Cargar datos globales
user_histories = load_histories()
users = load_users()

# Estado de sesión
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "history" not in st.session_state:
    st.session_state.history = []

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
                st.session_state.history = user_histories.get(username, [])
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
                    user_histories[username] = []  # Inicializar histórico vacío
                    save_histories(user_histories)
                    st.success(f"Usuario {username} registrado exitosamente. Ahora puedes iniciar sesión.")
            else:
                st.error("Por favor, ingresa un usuario y contraseña válidos.")
else:
    # Pantalla principal con logout
    st.sidebar.button("Cerrar Sesión", on_click=lambda: (
        save_histories({**user_histories, st.session_state.user_id: st.session_state.history}),
        st.session_state.update({"logged_in": False, "user_id": None, "history": []}),
        st.rerun()
    ))
    
    st.subheader(f"Sesión de: {st.session_state.user_id}")
    
    # Display the chat history with feedback
    for idx, item in enumerate(st.session_state.history):
        if len(item) == 3:  # Nuevo formato con tiempo
            q, a, t = item
            st.markdown(f"**Tú:** {q}")
            st.markdown(f"**SoeBOT:** {a}")
            st.markdown(f"**Tiempo de respuesta:** {t:.2f} segundos")
            
            # Agregar opciones de feedback para cada respuesta
            with st.expander("📝 Enviar Feedback (opcional)"):
                col1, col2, col3 = st.columns(3)
                satisfaction = col1.slider("Satisfacción", 1, 5, 3, key=f"sat_{idx}")
                clarity = col2.slider("Claridad", 1, 5, 3, key=f"clar_{idx}")
                completeness = col3.slider("Completitud", 1, 5, 3, key=f"comp_{idx}")
                
                error_type = st.selectbox("¿Hubo algún error?", ["Ninguno", "Contexto insuficiente", "Alucinación", "Interpretación errónea", "Formato incorrecto"], key=f"err_{idx}")
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
                            st.success("✅ Feedback guardado exitosamente. ¡Gracias!")
                        else:
                            st.error("Error al enviar feedback.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:  # Formato antiguo sin tiempo
            q, a = item
            st.markdown(f"**Tú:** {q}")
            st.markdown(f"**SoeBOT:** {a}")
    
    question = st.text_input("Escribe tu pregunta:", key="input_box")
    
    if st.button("Preguntar") and question.strip():
        # Add the new question to the history and display it immediately
        st.markdown(f"**Tú:** {question}")
        
        # Create a placeholder for the streaming answer
        answer_placeholder = st.markdown("**SoeBOT:** ")
        
        # Use a mutable dict to store the full answer from the stream
        answer_wrapper = {"text": ""}
        
        try:
            with st.spinner("Consultando a la IA..."):
                start_time = time.time()
                print(f"--- CLIENTE: [{start_time}] Iniciando petición para usuario {st.session_state.user_id}.")
                
                # Define the generator for st.write_stream
                def stream_generator():
                    first_chunk = True
                    with requests.post(
                        "http://127.0.0.1:9000/ask",
                        json={"question": question, "user_id": st.session_state.user_id},  # Agregar user_id (opcional para servidor)
                        stream=True
                    ) as response:
                        response.raise_for_status()  # Raise an exception for bad status codes
                        for chunk in response.iter_content(chunk_size=None):
                            if first_chunk:
                                first_chunk_time = time.time()
                                print(f"--- CLIENTE: [{first_chunk_time}] Recibido el primer chunk. Tiempo hasta el primer chunk: {first_chunk_time - start_time:.2f}s")
                                first_chunk = False
                            if chunk:
                                decoded_chunk = chunk.decode('utf-8')
                                answer_wrapper["text"] += decoded_chunk
                                yield decoded_chunk
                
                # Use write_stream to display the content as it arrives
                answer_placeholder.write_stream(stream_generator())
            
            end_time = time.time()
            response_time = end_time - start_time  # Calcular tiempo total
            print(f"--- CLIENTE: [{end_time}] Stream finalizado. Tiempo total: {response_time:.2f}s")
            
            # Mostrar tiempo en la UI
            st.markdown(f"**Tiempo de respuesta:** {response_time:.2f} segundos")
            
            # Once the stream is complete, save the full answer to the session state
            st.session_state.history.append((question, answer_wrapper["text"], response_time))  # Agregado tiempo
            
            # Guardar histórico automáticamente
            user_histories[st.session_state.user_id] = st.session_state.history
            save_histories(user_histories)
            
            # Clear the input box by rerunning the script
            st.rerun()
        
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: No se pudo conectar al servidor en http://127.0.0.1:9000. ¿Está el servidor `mcp_server_local.py` en ejecución?")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")
