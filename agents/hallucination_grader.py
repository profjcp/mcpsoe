import logging
from typing import Tuple

class HallucinationGrader:
    """
    Agente Evaluador de Alucinaciones (Hallucination Grader - Fase 3.1).
    Audita la respuesta generada por el RAG comparándola contra el contexto documental.
    Si la respuesta contiene afirmaciones no respaldadas, la marca como no grounded (is_grounded=False).
    """

    def __init__(self, llm=None):
        self.llm = llm

    def grade(self, context: str, response: str, question: str = "") -> Tuple[bool, str]:
        """
        Evalúa si la respuesta está completamente respaldada por el contexto.
        Devuelve Tuple[is_grounded: bool, reason: str].
        """
        if not response or not context:
            return True, "Contexto o respuesta vacíos."

        fallback_msg = "No dispongo de esa información en los reglamentos vigentes. Por favor, acude a la Jefatura Académica."
        if fallback_msg.lower() in response.lower():
            # Si el modelo correctamente devolvió la respuesta de contingencia por falta de contexto
            return True, "Respuesta de contingencia válida."

        if not self.llm:
            # Fallback heurístico simple si no hay LLM asignado al grader
            context_words = set(context.lower().split())
            response_words = set(w for w in response.lower().split() if len(w) > 3)
            if not response_words:
                return True, "Respuesta corta."
            overlap = len(context_words.intersection(response_words))
            ratio = overlap / len(response_words)
            is_valid = ratio >= 0.2
            return is_valid, f"Solapamiento heurístico: {ratio:.2f}"

        context_snippet = context[:2000] + ("..." if len(context) > 2000 else "")
        prompt = f"""<rol>
Eres un auditor estricto de control de calidad para un asistente universitario de posgrado.
Tu tarea es verificar si la RESPUESTA GENERADA contiene ÚNICAMENTE información respaldada por el CONTEXTO DE DOCUMENTOS.
</rol>

<contexto_normativo>
{context_snippet}
</contexto_normativo>

<pregunta_usuario>
{question}
</pregunta_usuario>

<respuesta_a_evaluar>
{response}
</respuesta_a_evaluar>

<instrucciones>
1. Analiza si las afirmaciones principales de la RESPUESTA tienen sustento directo en <contexto_normativo>.
2. Si la respuesta contiene hechos inventados o información ausente en el contexto, responde 'NO'.
3. Si la respuesta está respaldada o es la respuesta formal de contingencia por ausencia de datos, responde 'SI'.
4. Responde ÚNICAMENTE con una sola palabra: 'SI' o 'NO'.
</instrucciones>

DICTAMEN (SI/NO):"""

        try:
            eval_result = str(self.llm.invoke(prompt)).strip().upper()
            is_grounded = "SI" in eval_result or "SÍ" in eval_result
            reason = "Respuesta fundamentada en el contexto." if is_grounded else "Se detectaron afirmaciones no respaldadas en la normativa vigente."
            return is_grounded, reason
        except Exception as e:
            logging.warning(f"Error en HallucinationGrader: {e}")
            return True, f"Error en evaluación: {e}"
