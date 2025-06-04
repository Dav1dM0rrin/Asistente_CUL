# Archivo: chatbot/llm_service.py
# Este servicio encapsula la lógica para interactuar con el modelo de lenguaje Gemini.
# MODIFICADO PARA EL CHATBOT UNIVERSITARIO CUL

import google.generativeai as genai
from chatbot.config import GEMINI_API_KEY # Importa la clave API desde la configuración.
from chatbot.bot_logging import logger # Usa el logger configurado para la aplicación.
import json # Necesario para parsear respuestas JSON del LLM y formatear datos.

# --- Constantes y Configuración del Modelo ---
MODEL_NAME = 'gemini-1.5-flash-latest' # Modelo de Gemini a utilizar.
USER_ROLE = "user" # Rol del usuario en el historial de chat.
MODEL_ROLE = "model" # Rol del modelo (Gemini) en el historial de chat.

# Configuración global del SDK de Gemini.
try:
    genai.configure(api_key=GEMINI_API_KEY)
    generation_config = genai.types.GenerationConfig(
        # temperature=0.7, # Podrías ajustar la creatividad.
        # max_output_tokens=2048, # Ajustar según necesidad.
    )
    # safety_settings = [ ... ] # Ajustar filtros de contenido si es necesario.

    llm_model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
    )
    logger.info(f"Modelo Gemini ({MODEL_NAME}) configurado exitosamente para Chatbot CUL.")
except Exception as e:
    logger.critical(f"CRÍTICO: Error al configurar el SDK de Gemini: {e}. El servicio LLM no funcionará.", exc_info=True)
    llm_model = None

conversation_sessions_store = {}

# --- Prompt de Sistema Detallado para el Chatbot Universitario CUL ---
SYSTEM_PROMPT_TEXT = """
Eres 'Asistente CUL', un chatbot IA avanzado, amigable, empático y muy servicial, desarrollado para la Corporación Universitaria Latinoamericana (CUL). Tu objetivo principal es asistir a estudiantes, aspirantes y personal con sus consultas sobre la vida universitaria.

Tus Propósitos Principales son:
1.  **Información Académica**: Responder preguntas sobre:
    * Trámites académicos (inscripciones, matrículas, certificados, homologaciones, etc.).
    * Horarios de clases, asignaturas, y disponibilidad de aulas (si tienes acceso a esta información).
    * Calendario académico (fechas importantes, periodos de exámenes, vacaciones).
    * Programas ofrecidos (pregrados, posgrados, cursos de extensión).
    * Requisitos de admisión y proceso de inscripción.
2.  **Soporte Técnico Básico**: Ofrecer guía para problemas técnicos comunes como:
    * Acceso a plataformas virtuales (Moodle, sistema de notas).
    * Problemas con el correo institucional.
    * Conexión a la red Wi-Fi de la universidad.
    * Uso básico de software licenciado por la universidad.
3.  **Información General de la Universidad**:
    * Ubicación de campus, facultades, oficinas administrativas, biblioteca, cafeterías.
    * Servicios al estudiante (bienestar universitario, deportes, cultura, orientación psicológica).
    * Eventos universitarios.
    * Información de contacto de diferentes dependencias.
4.  **Generación de Tickets para Asistencia Humana**:
    * Si una consulta es demasiado compleja, requiere información personal sensible que no puedes manejar, o el usuario solicita explícitamente "hablar con un humano", "necesito ayuda de una persona", "generar un ticket", o frases similares, debes ofrecer generar un ticket para que un miembro del personal de la CUL se ponga en contacto.
    * Para generar un ticket, necesitarás una breve descripción del problema o consulta del usuario.

Capacidades Clave y Comportamiento Esperado:
-   **Lenguaje y Tono**: Usa un español colombiano claro, amigable, formal pero cercano, y respetuoso. Sé paciente y comprensivo.
-   **Clarificación**: Si la pregunta del usuario es ambigua, pide amablemente que la reformule o dé más detalles. No asumas.
-   **Veracidad**: ¡No inventes información! Si no tienes la información certera, es mejor decir "No tengo esa información en este momento, pero te sugiero consultar la página web oficial de la CUL ([enlacedelapaginaweb.cul.edu.co] si lo tienes) o contactar directamente con la oficina correspondiente." o "No encontré datos sobre eso."
-   **Concisión y Formato**: Mantén las respuestas razonablemente concisas y bien formateadas para Telegram.
-   **Contexto Local**: Recuerda que representas a la Corporación Universitaria Latinoamericana (CUL).
-   **Limitaciones**: Eres un IA. No puedes realizar acciones que requieran acceso a datos personales o sistemas internos sin la debida autorización o integración. Tu función es informar y guiar.
-   **Uso de Datos Externos (RAG)**: Si se te proporciona 'Contexto de la base de datos de FAQs' en un mensaje, úsalo para responder la consulta actual. No lo memorices para futuras preguntas no relacionadas.
-   **Comandos**: Recuerda al usuario comandos útiles como /ayuda, /contacto, /ticket, /reset_chat cuando sea apropiado.

Ejemplo de interacción para generar ticket:
Usuario: "No puedo ingresar a la plataforma de notas y ya intenté recuperar mi contraseña."
Tú: "Entiendo. Lamento que estés teniendo problemas para acceder a la plataforma de notas. Como ya intentaste recuperar tu contraseña sin éxito, puedo ayudarte a generar un ticket para que nuestro equipo de soporte técnico revise tu caso. ¿Te gustaría que lo hagamos?"
Usuario: "Sí, por favor."
Tú: "Perfecto. Por favor, dame una breve descripción del problema, incluyendo tu nombre completo y número de identificación estudiantil (si lo tienes a mano) para incluirlo en el ticket."
"""

async def generate_response(user_id: str, user_message: str, api_data_context: dict = None) -> str:
    """
    Genera una respuesta utilizando el LLM, manteniendo un historial de conversación por usuario.
    """
    if not llm_model:
        logger.error(f"LLM_SERVICE_CUL: Modelo Gemini no disponible para user_id {user_id}.")
        return "Lo siento, estoy experimentando dificultades técnicas con mi asistente inteligente en este momento. Por favor, intenta de nuevo más tarde."

    if user_id not in conversation_sessions_store:
        initial_history = [
            {"role": USER_ROLE, "parts": [{"text": SYSTEM_PROMPT_TEXT}]},
            {"role": MODEL_ROLE, "parts": [{"text": "¡Hola! Soy Asistente CUL. Estoy aquí para ayudarte con tus consultas sobre la Corporación Universitaria Latinoamericana. ¿En qué puedo colaborarte hoy? 🎓"}]}
        ]
        conversation_sessions_store[user_id] = llm_model.start_chat(history=initial_history)
        logger.info(f"LLM_SERVICE_CUL: Nueva sesión de chat iniciada para user_id {user_id}.")
    
    chat_session = conversation_sessions_store[user_id]

    message_parts_for_llm = [{"text": user_message}]
    if api_data_context:
        context_info_text = (
            "\n\n--- Contexto de la base de datos de FAQs (para tu información interna al responder la pregunta actual del usuario) ---\n"
            f"{json.dumps(api_data_context, indent=2, ensure_ascii=False)}\n"
            "--- Fin del contexto ---"
        )
        message_parts_for_llm.append({"text": context_info_text})
        logger.debug(f"LLM_SERVICE_CUL: Añadiendo contexto de API/FAQs al mensaje para user_id {user_id}: {context_info_text[:200]}...")

    try:
        logger.debug(f"LLM_SERVICE_CUL: Enviando mensaje a Gemini para user_id {user_id}. Mensaje (inicio): {str(message_parts_for_llm)[:300]}...")
        
        llm_api_response = await chat_session.send_message_async(message_parts_for_llm)
        
        if llm_api_response.prompt_feedback and llm_api_response.prompt_feedback.block_reason:
            block_reason = llm_api_response.prompt_feedback.block_reason
            block_message = f"Respuesta bloqueada por política de seguridad: {block_reason}."
            logger.warning(f"LLM_SERVICE_CUL: Respuesta de Gemini bloqueada para user_id {user_id}. Razón: {block_reason}. Feedback: {llm_api_response.prompt_feedback}")
            return f"No pude generar una respuesta completa debido a una restricción de contenido ({block_reason}). Por favor, reformula tu pregunta."

        generated_text = llm_api_response.text
        logger.info(f"LLM_SERVICE_CUL: Respuesta recibida de Gemini para user_id {user_id}: {generated_text[:300]}...")
        return generated_text

    except Exception as e:
        logger.error(f"LLM_SERVICE_CUL: Error al generar respuesta con Gemini para user_id {user_id}: {e}", exc_info=True)
        if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
            logger.error(f"LLM_SERVICE_CUL: Prompt Feedback de Gemini en error: {e.response.prompt_feedback}")
        return "Lo siento, tuve un problema técnico al intentar procesar tu solicitud con el asistente inteligente. Por favor, intenta de nuevo en unos momentos."


async def classify_intent_and_extract_entities(user_message: str) -> dict:
    """
    Utiliza el LLM para clasificar la intención y extraer entidades relevantes para el contexto universitario.
    """
    if not llm_model:
        logger.error("LLM_SERVICE_CUL: Modelo Gemini no disponible para clasificación de intención.")
        return {"error": "Modelo Gemini no disponible."}

    classification_prompt_text = f"""
    Analiza el siguiente mensaje de usuario en el contexto de la Corporación Universitaria Latinoamericana (CUL) y determina su intención principal y extrae entidades relevantes.
    Intenciones posibles:
    - CONSULTA_TRAMITE_ACADEMICO (ej: "¿cómo me inscribo?", "costo de la matrícula", "¿qué necesito para un certificado?")
    - CONSULTA_HORARIO (ej: "¿cuándo tengo clase de cálculo?", "horario de la biblioteca")
    - CONSULTA_PROGRAMA_ACADEMICO (ej: "información sobre ingeniería de sistemas", "¿tienen posgrados en derecho?")
    - SOLICITUD_SOPORTE_TECNICO (ej: "no puedo entrar a Moodle", "problemas con el wifi")
    - INFORMACION_GENERAL_CUL (ej: "¿dónde queda la cafetería?", "teléfono de admisiones")
    - GENERAR_TICKET_HUMANO (ej: "quiero hablar con una persona", "necesito ayuda de un asesor", "generar un ticket")
    - SALUDO
    - DESPEDIDA
    - AFIRMACION
    - NEGACION
    - CANCELAR_ACCION
    - PREGUNTA_GENERAL_CHATBOT (ej: "¿quién eres?", "¿qué puedes hacer?")
    - DESCONOCIDO

    Para CONSULTA_TRAMITE_ACADEMICO, extrae si es posible: "nombre_tramite" (string), "documento_relacionado" (string).
    Para CONSULTA_HORARIO, extrae si es posible: "nombre_asignatura" (string), "dia_semana" (string), "lugar" (string, ej: "biblioteca", "laboratorio X").
    Para CONSULTA_PROGRAMA_ACADEMICO, extrae: "nombre_programa" (string), "nivel_academico" (string, ej: "pregrado", "posgrado", "diplomado").
    Para SOLICITUD_SOPORTE_TECNICO, extrae: "descripcion_problema" (string), "plataforma_afectada" (string, ej: "Moodle", "correo", "wifi").
    Para GENERAR_TICKET_HUMANO, extrae: "resumen_solicitud_ticket" (string, un breve resumen de por qué necesita el ticket).
    Para INFORMACION_GENERAL_CUL, extrae: "tema_consulta_general" (string, ej: "ubicación", "contacto", "servicio").

    Mensaje del usuario: "{user_message}"

    Responde ÚNICAMENTE en formato JSON válido con las claves "intent" (string) y "entities" (objeto JSON).
    Si no se extraen entidades, "entities" debe ser un objeto vacío {{}}.
    Si la intención no es clara o no encaja en las categorías, usa "DESCONOCIDO".

    Ejemplos de respuesta JSON esperada:
    Si el usuario dice "¿cuáles son los requisitos para la inscripción a psicología?":
    {{
      "intent": "CONSULTA_TRAMITE_ACADEMICO",
      "entities": {{
        "nombre_tramite": "inscripción",
        "documento_relacionado": "requisitos",
        "nombre_programa": "psicología" 
      }}
    }}

    Si el usuario dice "Necesito ayuda, no me funciona el correo institucional":
    {{
      "intent": "SOLICITUD_SOPORTE_TECNICO",
      "entities": {{
        "descripcion_problema": "no funciona el correo institucional",
        "plataforma_afectada": "correo institucional"
      }}
    }}
    
    Si el usuario dice "Quiero hablar con alguien de admisiones":
    {{
      "intent": "GENERAR_TICKET_HUMANO",
      "entities": {{
        "resumen_solicitud_ticket": "hablar con alguien de admisiones"
      }}
    }}
    """
    try:
        logger.debug(f"LLM_SERVICE_CUL: Enviando prompt de clasificación/extracción a Gemini (inicio): {classification_prompt_text[:300]}...")
        
        llm_classification_response = await llm_model.generate_content_async(classification_prompt_text)
        
        if llm_classification_response.prompt_feedback and llm_classification_response.prompt_feedback.block_reason:
            block_reason = llm_classification_response.prompt_feedback.block_reason
            logger.warning(f"LLM_SERVICE_CUL: Respuesta de clasificación de Gemini bloqueada. Razón: {block_reason}.")
            return {"intent": "DESCONOCIDO", "entities": {}, "error": f"Respuesta de clasificación bloqueada ({block_reason})", "raw_response": ""}

        raw_json_text = llm_classification_response.text
        logger.info(f"LLM_SERVICE_CUL: Respuesta de clasificación (raw JSON) de Gemini: {raw_json_text}")

        clean_json_text = raw_json_text.strip()
        if clean_json_text.startswith("```json"):
            clean_json_text = clean_json_text[7:-3].strip()
        elif clean_json_text.startswith("```"):
             clean_json_text = clean_json_text[3:-3].strip()
        
        parsed_response = json.loads(clean_json_text)
        
        if not isinstance(parsed_response, dict) or \
           "intent" not in parsed_response or \
           not isinstance(parsed_response.get("intent"), str) or \
           "entities" not in parsed_response or \
           not isinstance(parsed_response.get("entities"), dict):
            raise ValueError("El JSON de respuesta del LLM para clasificación no tiene la estructura esperada (intent/entities).")
            
        logger.info(f"LLM_SERVICE_CUL: Intención y entidades extraídas: {parsed_response}")
        return parsed_response

    except json.JSONDecodeError as json_err:
        logger.error(f"LLM_SERVICE_CUL: Error al parsear JSON de Gemini para clasificación: {json_err}. Respuesta original: {raw_json_text}", exc_info=True)
        return {"intent": "DESCONOCIDO", "entities": {}, "error": "Error al parsear la estructura de la respuesta del LLM.", "raw_response": raw_json_text}
    except Exception as e:
        logger.error(f"LLM_SERVICE_CUL: Error en clasificación de intención con Gemini: {e}", exc_info=True)
        if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
            logger.error(f"LLM_SERVICE_CUL: Prompt Feedback de Gemini (clasificación) en error: {e.response.prompt_feedback}")
        return {"intent": "DESCONOCIDO", "entities": {}, "error": f"Error inesperado durante la clasificación: {type(e).__name__}"}


async def reset_conversation_history(user_id: str) -> bool:
    """
    Limpia/resetea el historial de conversación para un usuario específico.
    """
    if user_id in conversation_sessions_store:
        del conversation_sessions_store[user_id]
        logger.info(f"LLM_SERVICE_CUL: Historial de conversación reseteado para el usuario {user_id}.")
        return True
    logger.info(f"LLM_SERVICE_CUL: No se encontró historial para resetear para el usuario {user_id}.")
    return False
