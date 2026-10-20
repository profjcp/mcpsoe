import re
import unicodedata

INSTITUTIONAL_FALLBACK_MSG = "No dispongo de esa información en los reglamentos vigentes. Por favor, acude a la Jefatura Académica."

def normalize_text(text: str) -> str:
    """Normaliza texto para matching robusto (minúsculas y sin acentos)."""
    text = (text or "").lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def is_out_of_domain_query(text: str) -> bool:
    """
    Detecta si la consulta trata explícitamente sobre instituciones externas,
    otros posgrados o universidades ajenas a la FICCT - UAGRM.
    """
    normalized = normalize_text(text)

    # Excepciones válidas: trámites en UAGRM con procedencia externa (ej. convalidaciones/traspasos)
    rescue_keywords = ["convalidar", "convalidacion", "convalidaciones", "traspaso", "homologacion", "homologar"]
    if any(kw in normalized for kw in rescue_keywords):
        return False

    external_entities = [
        "harvard", "oxford", "stanford", "mit", "cambridge", "berkeley",
        "unam", "uba", "pucp", "usp", "unicamp", "itesm", "tecmilenio",
        "san simon", "umss", "umsa", "ucb", "catolica", "upsa", "univalle",
        "utebsa", "upds", "udabol", "nur", "unitepc", "emi", "ucatec", "uagrm pregrado"
    ]
    for entity in external_entities:
        if re.search(rf"\b{re.escape(entity)}\b", normalized):
            return True

    return False
