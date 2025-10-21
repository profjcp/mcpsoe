import streamlit as st
import requests

st.set_page_config(page_title="SoeBOT WebUI", page_icon="🤖")

st.title("SoeBOT - Chat con tu IA")

if "history" not in st.session_state:
    st.session_state.history = []

question = st.text_input("Escribe tu pregunta:")

if st.button("Preguntar") and question.strip():
    with st.spinner("Consultando a la IA..."):
        try:
            response = requests.post(
                "http://127.0.0.1:8000/ask",
                json={"question": question}
            )
            if response.ok:
                # Correctly extract the 'answer' field from the JSON response
                answer = response.json().get("answer", "No se recibió una respuesta válida.")
                st.session_state.history.append((question, answer))
            else:
                st.error(f"Error al consultar la API: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: No se pudo conectar al servidor en http://127.0.0.1:8000. ¿Está el servidor `uvicorn` en ejecución?")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")

st.write("### Historial")
for q, a in reversed(st.session_state.history):
    st.markdown(f"**Tú:** {q}")
    st.markdown(f"**SoeBOT:** {a}")
