from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import PromptTemplate
import uvicorn
import redis
import json
import os
import time
import numpy as np
import faiss
import pickle
from fastapi.responses import StreamingResponse
import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from datetime import datetime
import logging
import unicodedata

# Lazy import de NLTK para evitar errores de inicialización
def get_sentiment_analyzer():
    """Importa y retorna el analizador de sentimientos de NLTK bajo demanda"""
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer
        import nltk
        try:
            nltk.data.find('sentiment/vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        return SentimentIntensityAnalyzer()
    except Exception as e:
        logging.warning(f"NLTK sentiment analyzer not available: {e}")
        return None

sia = None  # Se inicializará en la primera solicitud

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('metrics.log'),
        logging.StreamHandler()
    ]
)

# --- Configuration ---
LLM_MODEL = "promptnow/llama-3-typhoon-v1.5-8b-instruct-q4_k_m"  # Cambiado al nuevo modelo para mejor precisión
EMBEDDING_MODEL = "nomic-embed-text"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
FAISS_INDEX_PATH = "faiss_index.bin"
CHUNKS_PATH = "chunks.pkl"
QA_FAISS_INDEX_PATH = "qa_faiss_index.bin"
QA_CACHE_PATH = "qa_cache.pkl"

# Redis connection will be initialized after app creation
r = None

# --- Global Objects ---
llm: OllamaLLM
embeddings: OllamaEmbeddings
faiss_index: faiss.Index
chunks: list
qa_faiss_index: faiss.Index
qa_cache: dict
faq_cache: dict = {}

# --- Métricas Prometheus (Cuantitativas) ---
query_counter = Counter('queries_total', 'Total queries processed')
response_time = Histogram('response_time_seconds', 'Response time in seconds')
cache_hit_counter = Counter('cache_hits_total', 'Total cache hits')
error_counter = Counter('errors_total', 'Total errors')
cpu_usage = Gauge('cpu_usage_percent', 'Current CPU usage')
memory_usage = Gauge('memory_usage_percent', 'Current memory usage')
sentiment_score = Gauge('response_sentiment', 'Average sentiment of responses')
hallucination_counter = Counter('hallucinations_total', 'Total hallucinations detected')

# --- Métricas Cualitativas Globales ---
qualitative_metrics = {
    "avg_satisfaction": [],
    "avg_clarity": [],
    "avg_completeness": [],
    "hallucination_rate": [],
    "avg_sentiment": [],
    "query_categories": {},
    "error_types": {},
    "response_times": []
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load all necessary models and data into memory.
    """
    global llm, embeddings, faiss_index, chunks, qa_faiss_index, qa_cache, faq_cache, r

    # 1. Load LLM and Embedding models
    print("--- Cargando Modelos de Ollama ---")
    try:
        # Ajustes optimizados para Llama 3 Typhoon: bajo temperature para precisión, alto top_k/top_p para diversidad sin alucinaciones
        llm = OllamaLLM(model=LLM_MODEL, temperature=0.2, top_k=50, top_p=0.95, num_ctx=8192)
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        llm.invoke("hello") # Test call
        print("Modelos de Ollama cargados exitosamente.")
    except Exception as e:
        print(f"\n[ERROR] No se pudieron cargar los modelos de Ollama. ¿Está Ollama en ejecución? Error: {e}")
        exit(1)

    # Initialize Redis
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        r.ping()
        print("Redis conectado exitosamente.")
    except Exception as e:
        print(f"[WARNING] No se pudo conectar a Redis: {e}")
        r = None

    # 2. Load FAISS indices and chunks
    print("--- Cargando índices FAISS y chunks ---")
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNKS_PATH):
        try:
            faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            with open(CHUNKS_PATH, 'rb') as f:
                chunks = pickle.load(f)
            print(f"Índice FAISS cargado: {faiss_index.ntotal} chunks")
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el índice FAISS: {e}")
            exit(1)
    else:
        print("[ERROR] Índices FAISS no encontrados. Ejecutar preprocess.py primero.")
        exit(1)

    # 3. Load Q&A cache and FAISS index
    if os.path.exists(QA_CACHE_PATH) and os.path.exists(QA_FAISS_INDEX_PATH):
        try:
            with open(QA_CACHE_PATH, 'rb') as f:
                qa_cache = pickle.load(f)
            qa_faiss_index = faiss.read_index(QA_FAISS_INDEX_PATH)
            print(f"Caché Q&A cargado: {len(qa_cache)} pares")
            print(f"Índice Q&A FAISS cargado: {qa_faiss_index.ntotal} embeddings")
        except Exception as e:
            print(f"[WARNING] No se pudo cargar caché Q&A: {e}")
            qa_cache = {}
            qa_faiss_index = faiss.IndexFlatL2(768)
    else:
        qa_cache = {}
        qa_faiss_index = faiss.IndexFlatL2(768)
        print("Iniciando caché Q&A vacío")

    # 4. Warmup de FAQs por dominio para reducir latencia en T1
    faq_cache = {}
    faq_files = {
        "AtencionCliente": "documentos/faq_atencion_cliente.txt",
        "Academica": "documentos/faq_academica.txt",
        "Investigacion": "documentos/faq_investigacion.txt"
    }
    for domain, path in faq_files.items():
        faqs = cargar_faqs_con_embeddings(path, embeddings.embed_query)
        print(f"FAQ {domain} precargado: {len(faqs)} preguntas")

    yield

    # Cleanup
    print("Limpiando recursos...")
    if r:
        r.close()

app = FastAPI(lifespan=lifespan)

class AskRequest(BaseModel):
    question: str
    user_id: str = "anonymous"

class FeedbackRequest(BaseModel):
    question: str
    response: str
    satisfaction: int  # 1-5
    clarity: int  # 1-5
    completeness: int  # 1-5
    error_type: str = ""
    comments: str = ""

def detect_hallucination(response: str, context: str) -> bool:
    """Detectar si la respuesta contiene información no en el contexto."""
    context_words = set(context.lower().split())
    response_words = set(response.lower().split())
    overlap = len(context_words.intersection(response_words))
    return overlap < len(response_words) * 0.1 if response_words else False

def normalize_text(text: str) -> str:
    """Normaliza texto para matching robusto (minúsculas y sin acentos)."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def categorize_query(question: str) -> str:
    """Categorizar pregunta por tipo (categoría única)."""
    question_lower = normalize_text(question)
    categories = {
        "Costos": ["costo", "precio", "pago", "matricula", "arancel", "inversion"],
        "Contenidos": ["contenido", "modulo", "curso", "materia", "clase", "programa"],
        "Admisión": ["admision", "requisito", "inscripcion", "documentos", "aplicar"],
        "Horarios": ["horario", "hora", "clase", "fecha", "inicio", "calendario"],
        "Políticas": ["politica", "regla", "norma", "reglamento", "procedimiento"],
        "Docentes": ["profesor", "docente", "instructor", "maestro"]
    }
    for category, keywords in categories.items():
        if any(kw in question_lower for kw in keywords):
            return category
    return "Otro"

def categorize_query_multi(question: str) -> list:
    """Devuelve todas las categorías relevantes para la pregunta (multi-categoría)."""
    question_lower = normalize_text(question)
    categories = {
        "AtencionCliente": [
            "costo", "precio", "pago", "matricula", "arancel", "inversion",
            "inscripcion", "documento", "formulario", "hoja de vida", "tramitar", "tramite",
            "certificacion", "certificaciones", "intermedia", "intermedias", "copia legalizada",
            "avance academico", "certificado de calificaciones", "vencimiento de plan",
            "caja", "mensajero", "atencion", "horario de atencion", "donde queda",
            "ubicado", "correo", "apoyoacademico", "reprobar", "modulos puedo reprobar"
            , "tutor", "tutoria", "tutorias", "tutoría", "tutorías"
        ],
        "Academica": [
            "malla", "plan de estudio", "materia", "asignatura", "contenido", "programa",
            "curso", "modulo", "modulos", "docente", "profesor", "requisito de admision",
            "ciberseguridad", "ciberdefensa", "seguridad", "defensa", "inteligencia artificial"
        ],
        "Investigacion": [
            "linea de investigacion", "perfil", "tutor", "asesor", "tesis", "investigacion",
            "metodologia", "monografia"
        ]
    }
    matched = []
    for category, keywords in categories.items():
        if any(kw in question_lower for kw in keywords):
            matched.append(category)
    return matched if matched else ["Otro"]

def cargar_faqs_con_embeddings(faq_path: str, embed_fn):
    """Carga preguntas/respuestas del FAQ con cache por mtime y embeddings precalculados."""
    if not os.path.exists(faq_path):
        return []

    try:
        mtime = os.path.getmtime(faq_path)
        cached = faq_cache.get(faq_path)
        if cached and cached.get("mtime") == mtime:
            return cached.get("faqs", [])

        faqs = []
        with open(faq_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]

        current_question = None
        current_answer_lines = []

        def flush_current():
            nonlocal current_question, current_answer_lines, faqs
            if current_question and current_answer_lines:
                answer_text = "\n".join(current_answer_lines).strip()
                if answer_text:
                    faqs.append({
                        "pregunta": current_question,
                        "respuesta": answer_text,
                        "embedding": embed_fn(current_question)
                    })
            current_question = None
            current_answer_lines = []

        for raw_line in lines:
            line = raw_line.strip()

            if line.startswith("Pregunta:"):
                flush_current()
                current_question = line.replace("Pregunta:", "", 1).strip()
                continue

            if line.startswith("Respuesta:"):
                response_first_line = line.replace("Respuesta:", "", 1).strip()
                if response_first_line:
                    current_answer_lines.append(response_first_line)
                continue

            if current_question is not None:
                current_answer_lines.append(raw_line)

        flush_current()

        faq_cache[faq_path] = {
            "mtime": mtime,
            "faqs": faqs
        }
        logging.info(f"FAQ cargado/actualizado desde disco: {faq_path} ({len(faqs)} preguntas)")
        return faqs
    except Exception as e:
        logging.warning(f"Error cargando FAQ de {faq_path}: {e}")
        return []

def buscar_faq_semantico(question: str, faqs: list, embed_fn, threshold: float = 0.75):
    """Busca la pregunta más similar en el FAQ usando similitud de embeddings."""
    if not faqs:
        return None
    try:
        q_emb = np.array(embed_fn(question))
        sims = []
        for f in faqs:
            f_emb = np.array(f["embedding"])
            # Similitud de coseno
            sim = np.dot(q_emb, f_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(f_emb) + 1e-8)
            sims.append(sim)
        
        max_idx = int(np.argmax(sims))
        if sims[max_idx] >= threshold:
            faq = faqs[max_idx]
            return f"Pregunta: {faq['pregunta']}\nRespuesta: {faq['respuesta']}"
    except Exception as e:
        logging.warning(f"Error en búsqueda semántica de FAQ: {e}")
    return None

@app.post("/ask")
async def ask(request: AskRequest):
    """
    Generates a streaming answer using RAG with FAISS and Redis caching.
    Primero busca en FAQs por dominio, luego en RAG si no encuentra.
    """
    print(f"Recibida pregunta: {request.question}")
    query_counter.inc()
    
    # Categorizar consulta (multi-categoría)
    categories = categorize_query_multi(request.question)
    qualitative_metrics["query_categories"][str(categories)] = qualitative_metrics["query_categories"].get(str(categories), 0) + 1
    print(f"Categorías detectadas: {categories}")

    # 0. Buscar en FAQs por dominio ANTES que en RAG
    faq_files = {
        "AtencionCliente": "documentos/faq_atencion_cliente.txt",
        "Academica": "documentos/faq_academica.txt",
        "Investigacion": "documentos/faq_investigacion.txt"
    }
    faq_responses = []
    for cat in categories:
        if cat in faq_files:
            print(f"Buscando en FAQ de {cat}...")
            faqs = cargar_faqs_con_embeddings(faq_files[cat], embeddings.embed_query)
            faq_response = buscar_faq_semantico(request.question, faqs, embeddings.embed_query, threshold=0.75)
            if faq_response:
                faq_responses.append(f"Respuesta ({cat}):\n{faq_response}")
                print(f"Encontrada respuesta en FAQ de {cat}")
    
    if faq_responses:
        print(f"Devolviendo {len(faq_responses)} respuesta(s) de FAQ")
        async def stream_faq_response():
            combined_response = "\n\n".join(faq_responses)
            # Guardar en caché también
            qa_cache[request.question] = combined_response
            qa_faiss_index.add(np.array([embeddings.embed_query(request.question)], dtype="float32"))
            try:
                faiss.write_index(qa_faiss_index, QA_FAISS_INDEX_PATH)
                with open(QA_CACHE_PATH, "wb") as f:
                    pickle.dump(qa_cache, f)
            except Exception as e:
                logging.error(f"Error guardando caché: {e}")
            yield combined_response
        return StreamingResponse(stream_faq_response(), media_type="text/event-stream")

    # 1. Check cache first (exact match)
    if request.question in qa_cache:
        print("Respuesta encontrada en caché de Q&A (coincidencia exacta).")
        cache_hit_counter.inc()
        async def stream_cached_response():
            yield qa_cache[request.question]
        return StreamingResponse(stream_cached_response(), media_type="text/event-stream")

    # 2. Embed the question
    start_embed = time.time()
    question_embedding = embeddings.embed_query(request.question)
    question_embedding_np = np.array([question_embedding], dtype="float32")
    print(f"Embedding de la pregunta generado en {time.time() - start_embed:.2f}s")

    # 3. Find similar Q&A pairs (Few-shot learning)
    similar_qa_examples = ""
    if qa_faiss_index.ntotal > 0:
        print("Buscando preguntas similares en el índice de Q&A...")
        distances, indices = qa_faiss_index.search(question_embedding_np, k=min(3, qa_faiss_index.ntotal))
        similar_questions = [list(qa_cache.keys())[i] for i in indices[0]]
        
        example_list = []
        for q in similar_questions:
            if q in qa_cache:
                example_list.append(f"Pregunta: {q}\nRespuesta: {qa_cache[q]}")
        
        if example_list:
            similar_qa_examples = "\n\n---\n\nEjemplos de preguntas y respuestas anteriores:\n\n" + "\n\n".join(example_list)
            print(f"Encontrados {len(example_list)} ejemplos de Q&A similares.")

    # 4. Perform RAG search for document chunks (aumentado a 5 chunks para más contexto)
    print("Realizando búsqueda RAG con FAISS para documentos...")
    start_faiss = time.time()
    distances, indices = faiss_index.search(question_embedding_np, 5)  # Cambiado a top_k=5
    relevant_chunks = [chunks[i] for i in indices[0]]
    print(f"Búsqueda en FAISS completada en {time.time() - start_faiss:.4f}s")

    if relevant_chunks:
        knowledge_context = "\n\n---\n\n".join(relevant_chunks)
        print(f"Contexto encontrado: {len(relevant_chunks)} chunks.")
    else:
        knowledge_context = "No se encontró información relevante en los documentos."

    # 5. Build the improved prompt with better instructions
    template = '''
Eres un asistente experto en responder preguntas basadas únicamente en el contexto proporcionado. No inventes información ni respondas fuera del contexto.

Instrucciones:
- Responde de manera concisa, clara y en el mismo idioma que la pregunta.
- Si la respuesta no está en el contexto, di "No tengo suficiente información para responder esta pregunta".
- Cita partes relevantes del contexto si es posible.
- Usa los ejemplos de Q&A anteriores como guía para el estilo de respuesta.

Contexto de documentos:
{context}

Ejemplos de preguntas y respuestas anteriores:
{few_shot_examples}

Pregunta actual: {question}

Respuesta:
'''
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm

    async def stream_generator():
        full_response = ""
        start_time = time.time()
        print("Iniciando llamada a chain.astream...")
        async for chunk in chain.astream({"context": knowledge_context, "question": request.question, "few_shot_examples": similar_qa_examples}):
            full_response += chunk
            yield chunk
        print("Stream del LLM finalizado.")
        
        # 6. Análisis cualitativo post-generación
        response_time_val = time.time() - start_time
        response_time.observe(response_time_val)
        qualitative_metrics["response_times"].append(response_time_val)

        # Hallucination detection
        is_hallucinated = detect_hallucination(full_response, knowledge_context)
        if is_hallucinated:
            hallucination_counter.inc()
            qualitative_metrics["hallucination_rate"].append(1)
            logging.warning(f"Posible alucinación detectada en respuesta a: {request.question}")
        else:
            qualitative_metrics["hallucination_rate"].append(0)

        # Sentiment analysis
        global sia
        if sia is None:
            sia = get_sentiment_analyzer()
        
        sentiment = 0
        if sia:
            try:
                sentiment = sia.polarity_scores(full_response)['compound']
                sentiment_score.set(sentiment)
                qualitative_metrics["avg_sentiment"].append(sentiment)
            except Exception as e:
                logging.warning(f"Sentiment analysis failed: {e}")
                qualitative_metrics["avg_sentiment"].append(0)
        else:
            qualitative_metrics["avg_sentiment"].append(0)

        # 7. Save the new Q&A to cache, FAISS index, and disk
        print("Guardando nueva Q&A para aprendizaje futuro...")
        qa_cache[request.question] = full_response
        qa_faiss_index.add(question_embedding_np)
        
        try:
            # Save updated FAISS index
            faiss.write_index(qa_faiss_index, QA_FAISS_INDEX_PATH)
            # Save updated Q&A cache
            with open(QA_CACHE_PATH, "wb") as f:
                pickle.dump(qa_cache, f)
            print("Índice y caché de Q&A actualizados en disco.")
        except Exception as e:
            logging.error(f"Error guardando caché: {e}")
            error_counter.inc()

        logging.info(f"Respuesta completada en {response_time_val:.2f}s | Categorías: {categories} | Hallucination: {is_hallucinated} | Sentiment: {sentiment:.2f}")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/feedback")
async def feedback(request: FeedbackRequest):
    """Recopilar feedback cualitativo del usuario."""
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "question": request.question,
        "response": request.response,
        "satisfaction": request.satisfaction,
        "clarity": request.clarity,
        "completeness": request.completeness,
        "error_type": request.error_type,
        "comments": request.comments
    }
    
    # Guardar feedback
    with open("feedback.jsonl", "a") as f:
        json.dump(feedback_data, f)
        f.write("\n")

    # Actualizar métricas globales
    qualitative_metrics["avg_satisfaction"].append(request.satisfaction)
    qualitative_metrics["avg_clarity"].append(request.clarity)
    qualitative_metrics["avg_completeness"].append(request.completeness)
    
    if request.error_type:
        qualitative_metrics["error_types"][request.error_type] = qualitative_metrics["error_types"].get(request.error_type, 0) + 1

    logging.info(f"Feedback recibido: Satisfacción={request.satisfaction}, Claridad={request.clarity}, Completitud={request.completeness}")
    
    return {"message": "Feedback guardado", "status": "success"}

@app.get("/metrics")
async def metrics():
    """Exponer todas las métricas (cuantitativas y cualitativas)."""
    cpu_usage.set(psutil.cpu_percent())
    memory_usage.set(psutil.virtual_memory().percent)
    
    # Calcular promedios cualitativos
    metrics_summary = {
        "quantitative": {
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "queries_total": query_counter._value.get() if hasattr(query_counter, '_value') else 0,
            "cache_hits_total": cache_hit_counter._value.get() if hasattr(cache_hit_counter, '_value') else 0,
            "errors_total": error_counter._value.get() if hasattr(error_counter, '_value') else 0,
            "hallucinations_total": hallucination_counter._value.get() if hasattr(hallucination_counter, '_value') else 0
        },
        "qualitative": {
            "avg_satisfaction": round(np.mean(qualitative_metrics["avg_satisfaction"]), 2) if qualitative_metrics["avg_satisfaction"] else 0,
            "avg_clarity": round(np.mean(qualitative_metrics["avg_clarity"]), 2) if qualitative_metrics["avg_clarity"] else 0,
            "avg_completeness": round(np.mean(qualitative_metrics["avg_completeness"]), 2) if qualitative_metrics["avg_completeness"] else 0,
            "hallucination_rate": round(np.mean(qualitative_metrics["hallucination_rate"]), 4) if qualitative_metrics["hallucination_rate"] else 0,
            "avg_sentiment": round(np.mean(qualitative_metrics["avg_sentiment"]), 2) if qualitative_metrics["avg_sentiment"] else 0,
            "avg_response_time": round(np.mean(qualitative_metrics["response_times"]), 2) if qualitative_metrics["response_times"] else 0,
            "query_categories": qualitative_metrics["query_categories"],
            "error_types": qualitative_metrics["error_types"],
            "total_queries_tracked": len(qualitative_metrics["hallucination_rate"])
        }
    }
    
    return metrics_summary

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)