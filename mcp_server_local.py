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
import re

from agents.faq_agent import FAQAgent
from agents.rag_doc_agent import DocRAGAgent
from agents.graph_rag_agent import GraphRAGAgent
from orchestrator.router import MultiAgentOrchestrator

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
GRAPH_INDEX_PATH = "graph_index.pkl"
INTERACTION_LOG_PATH = "interaction_logs.jsonl"
FEEDBACK_LOG_PATH = "feedback.jsonl"
USER_HISTORIES_PATH = "user_histories.json"
ENABLE_GRAPH_RAG = os.getenv("ENABLE_GRAPH_RAG", "1") == "1"

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
faq_agent = None
doc_rag_agent = None
graph_rag_agent = None
orchestrator = None

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

# --- Métricas por usuario (en memoria desde el último reinicio) ---
per_user_metrics = {}


def ensure_user_metrics(user_id: str):
    """Inicializa y retorna la estructura de métricas por usuario."""
    user_key = user_id or "anonymous"
    if user_key not in per_user_metrics:
        per_user_metrics[user_key] = {
            "queries_total": 0,
            "faq_hits_total": 0,
            "cache_hits_total": 0,
            "guidance_total": 0,
            "rag_total": 0,
            "history_import_total": 0,
            "errors_total": 0,
            "hallucinations_total": 0,
            "response_times": [],
            "satisfaction": [],
            "clarity": [],
            "completeness": [],
            "query_categories": {},
            "error_types": {}
        }
    return per_user_metrics[user_key], user_key


def append_jsonl_record(path: str, payload: dict):
    """Guarda un registro JSONL sin sobrescribir el histórico existente."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logging.warning(f"Error guardando registro en {path}: {e}")


def read_jsonl_records(path: str) -> list:
    """Lee un archivo JSONL y devuelve sus registros."""
    if not os.path.exists(path):
        return []
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    except Exception as e:
        logging.warning(f"Error leyendo registros de {path}: {e}")
    return records


def safe_float(value, default=0.0):
    """Convierte a float sin lanzar excepciones."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_interaction_signature(user_id: str, question: str, response_text: str, response_time_val: float) -> str:
    """Crea una firma estable para evitar duplicados al importar historial."""
    normalized_user = (user_id or "anonymous").strip().lower()
    normalized_question = " ".join(str(question or "").split())
    normalized_response = " ".join(str(response_text or "").split())[:500]
    normalized_time = round(safe_float(response_time_val, 0.0), 4)
    return f"{normalized_user}|{normalized_question}|{normalized_response}|{normalized_time}"


def backfill_interaction_logs_from_histories():
    """Importa al log central las conversaciones históricas guardadas por usuario."""
    if not os.path.exists(USER_HISTORIES_PATH):
        return 0

    existing_signatures = set()
    for record in read_jsonl_records(INTERACTION_LOG_PATH):
        existing_signatures.add(
            build_interaction_signature(
                record.get("user_id", "anonymous"),
                record.get("question", ""),
                record.get("response_text") or record.get("response_preview", ""),
                record.get("response_time_s", 0),
            )
        )

    imported = 0
    imported_at = datetime.now().isoformat()
    history_mtime = datetime.fromtimestamp(os.path.getmtime(USER_HISTORIES_PATH)).isoformat()

    try:
        with open(USER_HISTORIES_PATH, "r", encoding="utf-8") as f:
            user_histories = json.load(f)
    except Exception as e:
        logging.warning(f"No se pudo cargar {USER_HISTORIES_PATH} para backfill: {e}")
        return 0

    for user_id, data in user_histories.items():
        conversations = data.get("conversations", []) or []
        for conv in conversations:
            chat_id = conv.get("id", "")
            chat_title = conv.get("title", "")
            for message in conv.get("messages", []) or []:
                question = ""
                response_text = ""
                response_time_val = 0.0
                message_timestamp = history_mtime

                if isinstance(message, dict):
                    question = str(message.get("question", "")).strip()
                    response_text = str(message.get("answer", "")).strip()
                    response_time_val = safe_float(message.get("response_time"), 0.0)
                    message_timestamp = message.get("timestamp") or history_mtime
                elif isinstance(message, (list, tuple)) and len(message) >= 2:
                    question = str(message[0]).strip()
                    response_text = str(message[1]).strip()
                    if len(message) >= 3:
                        response_time_val = safe_float(message[2], 0.0)
                    if len(message) >= 4 and message[3]:
                        message_timestamp = str(message[3])

                if not question and not response_text:
                    continue

                signature = build_interaction_signature(user_id, question, response_text, response_time_val)
                if signature in existing_signatures:
                    continue

                append_jsonl_record(
                    INTERACTION_LOG_PATH,
                    {
                        "timestamp": message_timestamp,
                        "imported_at": imported_at,
                        "user_id": user_id or "anonymous",
                        "question": question,
                        "categories": categorize_query_multi(question),
                        "source": "HISTORY_IMPORT",
                        "response_time_s": round(response_time_val, 4),
                        "hallucinated": False,
                        "chat_id": chat_id,
                        "chat_title": chat_title,
                        "response_text": response_text,
                        "response_preview": response_text[:500],
                        "imported_from_history": True,
                    }
                )
                existing_signatures.add(signature)
                imported += 1

    logging.info(f"Backfill de historial completado: {imported} interacciones importadas a {INTERACTION_LOG_PATH}")
    return imported


def hydrate_metrics_from_persisted_data():
    """Reconstruye métricas globales y por usuario desde los archivos persistidos."""
    per_user_metrics.clear()
    qualitative_metrics["avg_satisfaction"] = []
    qualitative_metrics["avg_clarity"] = []
    qualitative_metrics["avg_completeness"] = []
    qualitative_metrics["hallucination_rate"] = []
    qualitative_metrics["avg_sentiment"] = []
    qualitative_metrics["query_categories"] = {}
    qualitative_metrics["error_types"] = {}
    qualitative_metrics["response_times"] = []

    for record in read_jsonl_records(INTERACTION_LOG_PATH):
        user_id = record.get("user_id", "anonymous")
        bucket, _ = ensure_user_metrics(user_id)
        bucket["queries_total"] += 1

        categories = record.get("categories") or categorize_query_multi(record.get("question", ""))
        for category in categories:
            bucket["query_categories"][category] = bucket["query_categories"].get(category, 0) + 1
        qualitative_metrics["query_categories"][str(categories)] = qualitative_metrics["query_categories"].get(str(categories), 0) + 1

        source = record.get("source", "RAG")
        if source == "FAQ":
            bucket["faq_hits_total"] += 1
        elif source == "CACHE":
            bucket["cache_hits_total"] += 1
        elif source == "GUIDANCE":
            bucket["guidance_total"] += 1
        elif source == "HISTORY_IMPORT":
            bucket["history_import_total"] += 1
        else:
            bucket["rag_total"] += 1

        response_time_val = safe_float(record.get("response_time_s"), None)
        if response_time_val is not None:
            bucket["response_times"].append(response_time_val)
            qualitative_metrics["response_times"].append(response_time_val)

        hallucinated = bool(record.get("hallucinated", False))
        if hallucinated:
            bucket["hallucinations_total"] += 1
            qualitative_metrics["hallucination_rate"].append(1)
        else:
            qualitative_metrics["hallucination_rate"].append(0)

    for record in read_jsonl_records(FEEDBACK_LOG_PATH):
        user_id = record.get("user_id", "anonymous")
        satisfaction = safe_float(record.get("satisfaction"), None)
        clarity = safe_float(record.get("clarity"), None)
        completeness = safe_float(record.get("completeness"), None)
        error_type = record.get("error_type", "")

        if satisfaction is not None:
            qualitative_metrics["avg_satisfaction"].append(satisfaction)
        if clarity is not None:
            qualitative_metrics["avg_clarity"].append(clarity)
        if completeness is not None:
            qualitative_metrics["avg_completeness"].append(completeness)

        if error_type:
            qualitative_metrics["error_types"][error_type] = qualitative_metrics["error_types"].get(error_type, 0) + 1

        if satisfaction is not None and clarity is not None and completeness is not None:
            record_feedback_metrics(user_id, int(satisfaction), int(clarity), int(completeness), error_type)


def record_interaction_metrics(
    user_id: str,
    question: str,
    categories: list,
    source: str,
    response_text: str,
    response_time_val: float,
    is_hallucinated: bool = False,
    sources: list = None,
    routing_trace: dict = None,
    confidence: float = 0.0,
    timing_ms: dict = None,
):
    """Registra métricas por usuario y persiste interacciones para análisis posteriores."""
    bucket, user_key = ensure_user_metrics(user_id)
    bucket["queries_total"] += 1
    bucket["response_times"].append(response_time_val)

    for category in categories or []:
        bucket["query_categories"][category] = bucket["query_categories"].get(category, 0) + 1

    if source == "FAQ":
        bucket["faq_hits_total"] += 1
    elif source == "CACHE":
        bucket["cache_hits_total"] += 1
    elif source == "GUIDANCE":
        bucket["guidance_total"] += 1
    elif source == "HISTORY_IMPORT":
        bucket["history_import_total"] += 1
    elif source in ("RAG", "RAG_DOC", "GRAPH_RAG"):
        bucket["rag_total"] += 1

    if is_hallucinated:
        bucket["hallucinations_total"] += 1

    append_jsonl_record(
        INTERACTION_LOG_PATH,
        {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_key,
            "question": question,
            "categories": categories,
            "source": source,
            "response_time_s": round(response_time_val, 4),
            "hallucinated": bool(is_hallucinated),
            "response_text": response_text,
            "response_preview": response_text[:500],
            "sources": sources or [],
            "routing_trace": routing_trace or {},
            "confidence": float(confidence or 0.0),
            "timing_ms": timing_ms or {},
        }
    )


def record_feedback_metrics(user_id: str, satisfaction: int, clarity: int, completeness: int, error_type: str):
    """Actualiza las métricas cualitativas por usuario."""
    bucket, _ = ensure_user_metrics(user_id)
    bucket["satisfaction"].append(satisfaction)
    bucket["clarity"].append(clarity)
    bucket["completeness"].append(completeness)
    if error_type:
        bucket["errors_total"] += 1
        bucket["error_types"][error_type] = bucket["error_types"].get(error_type, 0) + 1


def build_per_user_summary():
    """Resume las métricas por usuario para exponerlas en /metrics."""
    summary = {}
    for user_id, data in per_user_metrics.items():
        summary[user_id] = {
            "queries_total": data["queries_total"],
            "faq_hits_total": data["faq_hits_total"],
            "cache_hits_total": data["cache_hits_total"],
            "guidance_total": data["guidance_total"],
            "rag_total": data["rag_total"],
            "history_import_total": data["history_import_total"],
            "errors_total": data["errors_total"],
            "hallucinations_total": data["hallucinations_total"],
            "avg_response_time": round(np.mean(data["response_times"]), 2) if data["response_times"] else 0,
            "avg_satisfaction": round(np.mean(data["satisfaction"]), 2) if data["satisfaction"] else 0,
            "avg_clarity": round(np.mean(data["clarity"]), 2) if data["clarity"] else 0,
            "avg_completeness": round(np.mean(data["completeness"]), 2) if data["completeness"] else 0,
            "query_categories": data["query_categories"],
            "error_types": data["error_types"]
        }
    return summary

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load all necessary models and data into memory.
    """
    global llm, embeddings, faiss_index, chunks, qa_faiss_index, qa_cache, faq_cache, r, faq_agent, doc_rag_agent, graph_rag_agent, orchestrator

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

    # 5. Cargar índice de grafo (Sprint 2 - GraphRAG, opcional)
    graph_index = {}
    if ENABLE_GRAPH_RAG and os.path.exists(GRAPH_INDEX_PATH):
        try:
            with open(GRAPH_INDEX_PATH, "rb") as f:
                graph_index = pickle.load(f)
            print(f"Graph index cargado: {len(graph_index)} nodos")
        except Exception as e:
            print(f"[WARNING] No se pudo cargar graph index: {e}")
            graph_index = {}
    elif ENABLE_GRAPH_RAG:
        print(f"[WARNING] Graph index no encontrado en {GRAPH_INDEX_PATH}. Ejecutar preprocess.py para habilitar GraphRAG.")

    # 6. Inicializar agentes y orquestador Sprint 1+2 (GUIDANCE -> FAQ -> CACHE -> RAG_DOC/GRAPH_RAG)
    def _build_chain():
        template = """
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
"""
        prompt = PromptTemplate.from_template(template)
        return prompt | llm

    faq_agent = FAQAgent(
        faq_files=faq_files,
        load_faqs_fn=cargar_faqs_con_embeddings,
        embed_query_fn=embeddings.embed_query,
        threshold=0.82,
        min_token_overlap=2,
    )

    doc_rag_agent = DocRAGAgent(
        faiss_index=faiss_index,
        chunks=chunks,
        embed_query_fn=embeddings.embed_query,
        build_chain_fn=_build_chain,
        top_k=5,
    )

    graph_rag_agent = GraphRAGAgent(
        faiss_index=faiss_index,
        chunks=chunks,
        graph_index=graph_index,
        embed_query_fn=embeddings.embed_query,
        top_k=5,
        max_neighbors_per_chunk=2,
    ) if ENABLE_GRAPH_RAG else None

    orchestrator = MultiAgentOrchestrator(
        faq_agent=faq_agent,
        doc_rag_agent=doc_rag_agent,
        graph_rag_agent=graph_rag_agent,
        categorize_fn=categorize_query_multi,
        needs_guidance_fn=needs_guidance,
        build_guidance_fn=build_guidance_message,
        qa_cache_ref=qa_cache,
        enable_graph_rag=ENABLE_GRAPH_RAG,
    )

    imported_count = backfill_interaction_logs_from_histories()
    hydrate_metrics_from_persisted_data()
    print(f"Historial persistido inicializado. Interacciones históricas importadas: {imported_count}")

    yield

    # Cleanup
    print("Limpiando recursos...")
    if r:
        r.close()

app = FastAPI(lifespan=lifespan)

class EmbedRequest(BaseModel):
    text: str

class AskRequest(BaseModel):
    question: str
    user_id: str = "anonymous"

class FeedbackRequest(BaseModel):
    question: str
    response: str
    user_id: str = "anonymous"
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
                "ubicado", "correo", "apoyoacademico", "reprobar", "modulos puedo reprobar",
                "tutoria", "tutorias", "tutoría", "tutorías",
                "asesoria", "asesoría", "asesorias", "asesorías",
                "congelar", "congelarse", "congelacion",
                "fotocopia", "fotocopias", "titulo", "título", "cedula", "cédula",
                "fotografía", "fotografias", "inasistencia", "falta", "faltas", "asistencia",
                "nota", "aprobacion", "aprobación", "nota minima", "nota mínima",
                "certificado de notas", "certificado", "certificados",
                "moodle", "aula virtual", "tarea", "tareas", "calificaciones", "prorroga", "prórroga",
                "mensaje privado", "contrasena", "contraseña", "sesiones sincronas", "sesiones síncronas",
                "grabaciones", "videos de clases", "video de clases"
            ],
        "Academica": [
            "malla", "plan de estudio", "materia", "asignatura", "contenido", "programa",
            "curso", "modulo", "modulos", "docente", "profesor", "requisito de admision",
            "ciberseguridad", "ciberdefensa", "seguridad", "defensa", "inteligencia artificial",
            "convalidacion", "convalidar", "convalidación", "convalidaciones"
        ],
        "Investigacion": [
            "linea de investigacion", "perfil", "asesor", "tesis", "investigacion",
            "metodologia", "monografia", "trabajo final de grado", "predefensa",
            "director de trabajo final", "tema de investigacion", "titulo del trabajo",
            "tutor", "tutores", "obtener mi tutor", "director de tesis"
        ]
    }
    matched = []
    for category, keywords in categories.items():
        if any(kw in question_lower for kw in keywords):
            matched.append(category)
    return matched if matched else ["Otro"]


def is_research_sensitive_query(question: str, categories: list) -> bool:
    """Detecta consultas sensibles de investigación/defensa para evitar cache FAQ contaminado."""
    normalized = normalize_text(question)
    sensitive_keywords = [
        "tesis", "defensa", "predefensa", "tutor", "investigacion",
        "metodologia", "monografia", "trabajo final de grado",
        "director de tesis", "linea de investigacion"
    ]
    if any(k in normalized for k in sensitive_keywords):
        return True
    return any(cat in {"Investigacion"} for cat in (categories or []))

def should_bypass_cache_answer(question: str, categories: list, cached_response: str) -> bool:
    """Bypass cuando el cache devuelve FAQ de ubicacion para consulta de tesis/investigacion."""
    if not cached_response:
        return False
    if is_research_sensitive_query(question, categories):
        bad_markers = [
            "¿Dónde queda ubicado el SOE?",
            "Respuesta (AtencionCliente):",
            "Av. Bush entre el 2do y 3er Anillo"
        ]
        return any(m in cached_response for m in bad_markers)
    return False

def needs_guidance(question: str, categories: list) -> bool:
    """Detecta preguntas demasiado vagas para guiar al usuario antes de responder."""
    normalized = normalize_text(question)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", normalized)
    cleaned = " ".join(cleaned.split())

    if not cleaned:
        return True

    vague_exact = {
        "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches",
        "ayuda", "necesito ayuda", "quiero ayuda", "quiero informacion",
        "informacion", "mas informacion", "tengo una duda", "consulta",
        "quiero consultar", "quiero saber", "como hago", "que hago",
        "ayudame", "me ayudas", "no entiendo"
    }

    vague_starts = [
        "necesito", "quiero informacion", "quiero saber", "como hago",
        "que hago", "me ayudas", "ayudame", "no entiendo"
    ]

    if cleaned in vague_exact:
        return True

    if any(cleaned.startswith(prefix) for prefix in vague_starts) and len(cleaned.split()) <= 6:
        return True

    if categories == ["Otro"] and len(cleaned.split()) <= 5:
        return True

    return False

def build_guidance_message() -> str:
    """Mensaje guía para ayudar al usuario a formular preguntas más concretas."""
    return (
        "Puedo ayudarte mejor si escribes una pregunta concreta dentro del contexto de SoeBOT.\n\n"
        "Áreas que manejo:\n"
        "1. Atención al cliente: inscripciones, certificados, pagos, Moodle y trámites.\n"
        "2. Académica: programas, módulos, horarios y docentes.\n"
        "3. Investigación: tutor, monografía, defensa y curso de actualización.\n\n"
        "Ejemplos de preguntas útiles:\n"
        "- ¿Cómo puedo subir una tarea a Moodle?\n"
        "- ¿Cuáles son los horarios de Ciberseguridad?\n"
        "- ¿Cómo puedo obtener mi tutor?\n"
        "- ¿Cuáles son los documentos de inscripción?"
    )

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
    Sprint 1: routing multi-agente (GUIDANCE -> FAQ -> CACHE -> RAG_DOC)
    preservando streaming y métricas existentes.
    """
    global orchestrator
    print(f"Recibida pregunta: {request.question}")
    query_counter.inc()
    request_start = time.time()

    categories = categorize_query_multi(request.question)
    qualitative_metrics["query_categories"][str(categories)] = qualitative_metrics["query_categories"].get(str(categories), 0) + 1
    print(f"Categorías detectadas: {categories}")

    if orchestrator is None:
        # Fallback defensivo para no romper servicio si no se inicializó en lifespan
        print("[WARNING] Orquestador no inicializado, activando fallback mínimo.")
        guidance_message = build_guidance_message()
        async def stream_fallback():
            response_time_val = time.time() - request_start
            response_time.observe(response_time_val)
            qualitative_metrics["response_times"].append(response_time_val)
            qualitative_metrics["hallucination_rate"].append(0)
            record_interaction_metrics(request.user_id, request.question, categories, "GUIDANCE", guidance_message, response_time_val, False)
            yield guidance_message
        return StreamingResponse(stream_fallback(), media_type="text/event-stream")

    route_result = orchestrator.route_pre_llm(request.question)

    if route_result.answer_mode in ("GUIDANCE", "FAQ", "CACHE"):
        if route_result.answer_mode == "CACHE":
            # Evitar cache para consultas académicas/investigación sensibles o respuestas contaminadas
            cached_text = route_result.answer_text or ""
            bypass_sensitive = any(cat in {"Academica", "Investigacion"} for cat in categories)
            bypass_contaminated = should_bypass_cache_answer(request.question, categories, cached_text)

            if bypass_sensitive or bypass_contaminated:
                context, sources, retrieval_ms, q_np = doc_rag_agent.retrieve(request.question)
                route_result = type(route_result)(
                    answer_text="",
                    answer_mode="RAG_DOC",
                    confidence=0.0,
                    sources=sources,
                    routing_trace={
                        **(route_result.routing_trace or {}),
                        "cache_bypassed_for_sensitive_categories": bool(bypass_sensitive),
                        "cache_bypassed_for_contaminated_answer": bool(bypass_contaminated),
                        "cache_hit": False,
                        "rag_used": True,
                    },
                    timing_ms={**(route_result.timing_ms or {}), "retrieval": retrieval_ms},
                    knowledge_context=context,
                    question_embedding_np=q_np,
                )
            else:
                cache_hit_counter.inc()

        if route_result.answer_mode in ("GUIDANCE", "FAQ", "CACHE"):
            async def stream_pre_llm():
                response_time_val = time.time() - request_start
                response_time.observe(response_time_val)
                qualitative_metrics["response_times"].append(response_time_val)
                qualitative_metrics["hallucination_rate"].append(0)

                record_interaction_metrics(
                    request.user_id,
                    request.question,
                    categories,
                    route_result.answer_mode,
                    route_result.answer_text,
                    response_time_val,
                    False,
                    sources=route_result.sources,
                    routing_trace=route_result.routing_trace,
                    confidence=route_result.confidence,
                    timing_ms=route_result.timing_ms,
                )

                if route_result.answer_mode == "FAQ":
                    qa_cache[request.question] = route_result.answer_text
                    qa_faiss_index.add(np.array([embeddings.embed_query(request.question)], dtype="float32"))
                    try:
                        faiss.write_index(qa_faiss_index, QA_FAISS_INDEX_PATH)
                        with open(QA_CACHE_PATH, "wb") as f:
                            pickle.dump(qa_cache, f)
                    except Exception as e:
                        logging.error(f"Error guardando caché: {e}")

                yield route_result.answer_text

            return StreamingResponse(stream_pre_llm(), media_type="text/event-stream")

    # RAG_DOC / GRAPH_RAG
    if route_result.answer_mode == "RAG_DOC" and (route_result.question_embedding_np is None or not route_result.knowledge_context):
        context, sources, retrieval_ms, q_np = doc_rag_agent.retrieve(request.question)
        route_result.knowledge_context = context
        route_result.sources = sources
        route_result.question_embedding_np = q_np
        base_timing = dict(route_result.timing_ms or {})
        base_timing["retrieval"] = retrieval_ms
        route_result.timing_ms = base_timing

    if route_result.answer_mode == "GRAPH_RAG" and not route_result.knowledge_context and graph_rag_agent is not None:
        graph_result = graph_rag_agent.retrieve_with_graph(request.question)
        route_result.knowledge_context = graph_result.context
        route_result.sources = graph_result.sources
        route_result.question_embedding_np = np.array([embeddings.embed_query(request.question)], dtype="float32")
        base_timing = dict(route_result.timing_ms or {})
        base_timing.update(graph_result.timing_ms or {})
        route_result.timing_ms = base_timing
        route_result.routing_trace = {**(route_result.routing_trace or {}), "graph_trace": graph_result.graph_trace}
        route_result.confidence = float(graph_result.confidence)

    knowledge_context = route_result.knowledge_context
    question_embedding_np = route_result.question_embedding_np
    if question_embedding_np is None:
        question_embedding_np = np.array([embeddings.embed_query(request.question)], dtype="float32")
    similar_qa_examples = ""

    qa_keys = list(qa_cache.keys())
    if qa_faiss_index.ntotal > 0 and len(qa_keys) > 0:
        k = min(3, qa_faiss_index.ntotal, len(qa_keys))
        distances, indices = qa_faiss_index.search(question_embedding_np, k=k)
        example_list = []
        for i in indices[0]:
            if 0 <= i < len(qa_keys):
                q = qa_keys[i]
                if q in qa_cache:
                    example_list.append(f"Pregunta: {q}\nRespuesta: {qa_cache[q]}")
        if example_list:
            similar_qa_examples = "\n\n---\n\nEjemplos de preguntas y respuestas anteriores:\n\n" + "\n\n".join(example_list)

    async def stream_rag_doc():
        full_response = ""
        generation_ms = 0.0

        async for chunk, done_ms in doc_rag_agent.generate(
            request.question,
            knowledge_context,
            few_shot_examples=similar_qa_examples,
        ):
            if chunk is not None:
                full_response += chunk
                yield chunk
            if done_ms is not None:
                generation_ms = done_ms

        response_time_val = time.time() - request_start
        response_time.observe(response_time_val)
        qualitative_metrics["response_times"].append(response_time_val)

        is_hallucinated = detect_hallucination(full_response, knowledge_context)
        if is_hallucinated:
            hallucination_counter.inc()
            qualitative_metrics["hallucination_rate"].append(1)
        else:
            qualitative_metrics["hallucination_rate"].append(0)

        global sia
        if sia is None:
            sia = get_sentiment_analyzer()

        sentiment = 0
        if sia:
            try:
                sentiment = sia.polarity_scores(full_response)["compound"]
                sentiment_score.set(sentiment)
                qualitative_metrics["avg_sentiment"].append(sentiment)
            except Exception:
                qualitative_metrics["avg_sentiment"].append(0)
        else:
            qualitative_metrics["avg_sentiment"].append(0)

        qa_cache[request.question] = full_response
        qa_faiss_index.add(question_embedding_np)
        try:
            faiss.write_index(qa_faiss_index, QA_FAISS_INDEX_PATH)
            with open(QA_CACHE_PATH, "wb") as f:
                pickle.dump(qa_cache, f)
        except Exception as e:
            logging.error(f"Error guardando caché: {e}")
            error_counter.inc()

        timing_ms = dict(route_result.timing_ms or {})
        timing_ms["generation"] = float(generation_ms)
        timing_ms["total"] = float(response_time_val * 1000.0)

        record_interaction_metrics(
            request.user_id,
            request.question,
            categories,
            "GRAPH_RAG" if route_result.answer_mode == "GRAPH_RAG" else "RAG_DOC",
            full_response,
            response_time_val,
            is_hallucinated,
            sources=route_result.sources,
            routing_trace=route_result.routing_trace,
            confidence=route_result.confidence,
            timing_ms=timing_ms,
        )

    return StreamingResponse(stream_rag_doc(), media_type="text/event-stream")

@app.post("/feedback")
async def feedback(request: FeedbackRequest):
    """Recopilar feedback cualitativo del usuario."""
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "user_id": request.user_id,
        "question": request.question,
        "response": request.response,
        "satisfaction": request.satisfaction,
        "clarity": request.clarity,
        "completeness": request.completeness,
        "error_type": request.error_type,
        "comments": request.comments
    }
    
    # Guardar feedback sin perder histórico previo
    append_jsonl_record(FEEDBACK_LOG_PATH, feedback_data)

    # Actualizar métricas globales
    qualitative_metrics["avg_satisfaction"].append(request.satisfaction)
    qualitative_metrics["avg_clarity"].append(request.clarity)
    qualitative_metrics["avg_completeness"].append(request.completeness)
    
    if request.error_type:
        qualitative_metrics["error_types"][request.error_type] = qualitative_metrics["error_types"].get(request.error_type, 0) + 1

    record_feedback_metrics(request.user_id, request.satisfaction, request.clarity, request.completeness, request.error_type)

    logging.info(f"Feedback recibido de {request.user_id}: Satisfacción={request.satisfaction}, Claridad={request.clarity}, Completitud={request.completeness}")
    
    return {"message": "Feedback guardado", "status": "success"}

@app.get("/metrics")
async def metrics():
    """Exponer todas las métricas (cuantitativas y cualitativas)."""
    cpu_usage.set(psutil.cpu_percent())
    memory_usage.set(psutil.virtual_memory().percent)
    
    persisted_interactions = read_jsonl_records(INTERACTION_LOG_PATH)
    persisted_queries_total = len(persisted_interactions)
    persisted_cache_hits = sum(1 for record in persisted_interactions if record.get("source") == "CACHE")
    persisted_hallucinations = sum(1 for record in persisted_interactions if record.get("hallucinated"))
    source_counts = {}
    traces_present = 0
    graph_rag_total = 0
    for record in persisted_interactions:
        src = str(record.get("source", "UNKNOWN"))
        source_counts[src] = source_counts.get(src, 0) + 1
        if src == "GRAPH_RAG":
            graph_rag_total += 1
        if record.get("routing_trace"):
            traces_present += 1

    graph_rag_rate = round((graph_rag_total / persisted_queries_total) * 100, 2) if persisted_queries_total else 0.0
    trace_coverage_rate = round((traces_present / persisted_queries_total) * 100, 2) if persisted_queries_total else 0.0

    # Calcular promedios cualitativos
    metrics_summary = {
        "quantitative": {
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "queries_total": persisted_queries_total,
            "cache_hits_total": persisted_cache_hits,
            "errors_total": max(error_counter._value.get() if hasattr(error_counter, '_value') else 0, sum(qualitative_metrics["error_types"].values())),
            "hallucinations_total": persisted_hallucinations,
            "source_counts": source_counts,
            "graph_rag_total": graph_rag_total,
            "graph_rag_rate_percent": graph_rag_rate,
            "routing_trace_present_total": traces_present,
            "routing_trace_coverage_percent": trace_coverage_rate
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
            "total_queries_tracked": len(qualitative_metrics["response_times"])
        },
        "per_user": build_per_user_summary()
    }
    
    return metrics_summary

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/embed")
async def embed(request: EmbedRequest):
    """Generate embeddings for text using Ollama embeddings model."""
    try:
        embedding = embeddings.embed_query(request.text)
        return {"embedding": embedding}
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)