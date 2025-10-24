import streamlit as st
import requests
import time

st.set_page_config(page_title="SoeBOT WebUI", page_icon="🤖")

st.title("SoeBOT - Chat con tu IA")

# Initialize history if it doesn't exist
if "history" not in st.session_state:
    st.session_state.history = []

# Display the chat history
for q, a in st.session_state.history:
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
            print(f"--- CLIENTE: [{start_time}] Iniciando petición.")

            # Define the generator for st.write_stream
            def stream_generator():
                first_chunk = True
                with requests.post(
                    "http://127.0.0.1:8000/ask",
                    json={"question": question},
                    stream=True
                ) as response:
                    response.raise_for_status() # Raise an exception for bad status codes
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
            answer_placeholder.write_stream(stream_generator)
        
        end_time = time.time()
        print(f"--- CLIENTE: [{end_time}] Stream finalizado. Tiempo total: {end_time - start_time:.2f}s")

        # Once the stream is complete, save the full answer to the session state
        st.session_state.history.append((question, answer_wrapper["text"]))
        
        # Clear the input box by rerunning the script
        st.rerun()

    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: No se pudo conectar al servidor en http://127.0.0.1:8000. ¿Está el servidor `uvicorn` en ejecución?")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
