import logging

class QueryRewriter:
    """
    Agente Reescritor de Consultas (Query Rewriter - Fase 3.2).
    Refina y expande preguntas ambiguas para mejorar la precisión de búsqueda en FAISS y BM25.
    """

    def __init__(self, llm=None):
        self.llm = llm

    def rewrite(self, question: str, categories: list = None) -> str:
        """
        Reescribe la consulta del usuario agregando palabras clave contextuales.
        """
        question_clean = (question or "").strip()
        if not question_clean or len(question_clean.split()) < 3:
            return question_clean

        if not self.llm:
            # Reescritura por reglas rápidas si no hay LLM
            extra_keywords = []
            if categories:
                if "Academica" in categories:
                    extra_keywords.append("programa maestría módulos materias")
                if "Investigacion" in categories:
                    extra_keywords.append("tesis monografía tutor defensa")
                if "AtencionCliente" in categories:
                    extra_keywords.append("trámite inscripción requisitos posgrado")
            
            if extra_keywords:
                return f"{question_clean} {' '.join(extra_keywords)}"
            return question_clean

        prompt = f"""<rol>
Eres un asistente de búsqueda académica de posgrado. Tu función es optimizar la consulta del usuario para el índice de documentos normativos.
</rol>

<instrucciones>
1. Conserva la intención original.
2. Agrega términos normativos relevantes ('reglamento', 'requisitos', 'procedimiento').
3. Devuelve ÚNICAMENTE la consulta reescrita en una sola línea sin explicaciones.
</instrucciones>

<consulta_original>
{question_clean}
</consulta_original>

Consulta optimizada:"""

        try:
            rewritten = str(self.llm.invoke(prompt)).strip()
            return rewritten if rewritten else question_clean
        except Exception as e:
            logging.warning(f"Error en QueryRewriter: {e}")
            return question_clean
