# Archivo: chatbot/api_client.py
# Cliente HTTP asíncrono para interactuar con el backend del proyecto CUL.
# MODIFICADO PARA EL CHATBOT UNIVERSITARIO CUL

import httpx
from chatbot.config import API_BASE_URL
from chatbot.bot_logging import logger
import json
from typing import Optional, Dict, Any

DEFAULT_HTTP_TIMEOUT = httpx.Timeout(60.0, connect=5.0)

# --- Funciones de API eliminadas (relacionadas con accidentes) ---
# report_accident_api
# get_accidents_from_api
# get_accidente_by_id

async def create_ticket_api(ticket_payload: dict) -> Optional[Dict[str, Any]]:
    """
    Envía los datos para la creación de un nuevo ticket de soporte al backend.
    (Función Placeholder - Necesita implementación real del endpoint en el backend)

    Args:
        ticket_payload (dict): Un diccionario con los detalles del ticket.
                               Ej: {"user_id_telegram": "123", "user_name": "John Doe", 
                                    "problem_description": "No puedo acceder a Moodle", 
                                    "contact_info": "user@example.com"}

    Returns:
        dict | None: Un diccionario con la respuesta de la API si la creación fue exitosa
                     (ej. {"ticket_id": "TICKET123", "status": "creado"}),
                     o un diccionario con error, o None si falla la conexión.
    """
    # Asumimos un endpoint como "/tickets/" en tu API_BASE_URL
    # API_BASE_URL podría ser "http://localhost:8000/api/cul/v1"
    ticket_creation_url = f"{API_BASE_URL.rstrip('/')}/tickets/"
    logger.info(f"API_CLIENT_CUL: Intentando crear ticket. URL: {ticket_creation_url}. Payload: {str(ticket_payload)[:200]}...")

    # --- SIMULACIÓN DE LLAMADA A API (Placeholder) ---
    # En un caso real, aquí harías la llamada HTTP con httpx.AsyncClient
    # try:
    #     async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT) as client:
    #         response = await client.post(ticket_creation_url, json=ticket_payload)
    #         response.raise_for_status() # Lanza excepción para errores HTTP 4xx/5xx
    #         created_ticket_data = response.json()
    #         logger.info(f"API_CLIENT_CUL: Ticket creado exitosamente. Respuesta: {str(created_ticket_data)[:200]}...")
    #         return created_ticket_data
    # except httpx.HTTPStatusError as e:
    #     # ... manejo de errores HTTP ...
    #     logger.error(f"API_CLIENT_CUL: Error HTTP ({e.response.status_code}) al crear ticket. Detalle: {e.response.text[:200]}", exc_info=False)
    #     return {"error": True, "status_code": e.response.status_code, "detail": e.response.text}
    # except httpx.RequestError as e:
    #     # ... manejo de errores de red/conexión ...
    #     logger.error(f"API_CLIENT_CUL: Error de red/conexión al crear ticket. URL: {ticket_creation_url}. Error: {e}", exc_info=True)
    #     return {"error": True, "status_code": None, "detail": "Error de conexión al crear ticket."}
    # except Exception as e:
    #     logger.critical(f"API_CLIENT_CUL: Error inesperado en create_ticket_api. URL: {ticket_creation_url}. Error: {e}", exc_info=True)
    #     return {"error": True, "status_code": None, "detail": "Error inesperado y crítico."}
    
    # Simulación para desarrollo sin backend real:
    await asyncio.sleep(1) # Simula latencia de red
    if "error" in ticket_payload.get("problem_description", "").lower(): # Simula un error basado en payload
        logger.warning(f"API_CLIENT_CUL (Simulación): Simulación de error al crear ticket para: {ticket_payload.get('problem_description')}")
        return {"error": True, "status_code": 500, "detail": "Error simulado al crear ticket en el servidor."}
    else:
        simulated_ticket_id = f"CUL-TICKET-{abs(hash(json.dumps(ticket_payload))) % 10000}"
        logger.info(f"API_CLIENT_CUL (Simulación): Ticket simulado creado con ID: {simulated_ticket_id}")
        return {"success": True, "ticket_id": simulated_ticket_id, "message": "Ticket registrado en el sistema (simulación). Un asesor se contactará pronto."}


async def get_faq_from_api(query: str, subject: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Consulta la base de datos de Preguntas Frecuentes (FAQ) del backend.
    (Función Placeholder - Necesita implementación real del endpoint en el backend)

    Args:
        query (str): La pregunta del usuario para buscar en las FAQs.
        subject (str, optional): Un tema o categoría para filtrar la búsqueda.

    Returns:
        dict | None: Un diccionario con la respuesta de la FAQ si se encuentra,
                     o un diccionario con error, o None si falla la conexión/no se encuentra.
                     Ej: {"faq_id": "FAQ001", "question": "...", "answer": "...", "category": "Matrículas"}
    """
    faq_url = f"{API_BASE_URL.rstrip('/')}/faqs/"
    params = {"query": query}
    if subject:
        params["subject"] = subject
    
    logger.info(f"API_CLIENT_CUL: Consultando FAQs. URL: {faq_url}. Params: {params}")

    # --- SIMULACIÓN DE LLAMADA A API (Placeholder) ---
    # try:
    #     async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT) as client:
    #         response = await client.get(faq_url, params=params)
    #         response.raise_for_status()
    #         faq_data = response.json() # Podría ser una lista de FAQs o una sola
    #         logger.info(f"API_CLIENT_CUL: FAQs obtenidas: {str(faq_data)[:200]}...")
    #         return faq_data 
    # except httpx.HTTPStatusError as e:
    #     # ...
    # except httpx.RequestError as e:
    #     # ...
    # except Exception as e:
    #     # ...
    
    # Simulación:
    await asyncio.sleep(0.5)
    if "horario" in query.lower():
        logger.info(f"API_CLIENT_CUL (Simulación): FAQ simulada encontrada para '{query}'")
        return {
            "faq_id": "FAQ_HOR001",
            "question": "¿Dónde puedo consultar los horarios de clase?",
            "answer": "Puedes consultar los horarios de clase actualizados en la plataforma Moodle de la universidad, en la sección 'Mis Cursos', o en las carteleras informativas de tu facultad.",
            "category": "Académico - Horarios"
        }
    elif "inscripcion" in query.lower() or "matrícula" in query.lower() :
        logger.info(f"API_CLIENT_CUL (Simulación): FAQ simulada encontrada para '{query}'")
        return {
            "faq_id": "FAQ_MAT002",
            "question": "¿Cuáles son los pasos para la matrícula?",
            "answer": "El proceso de matrícula generalmente incluye: 1. Preinscripción en línea. 2. Pago de derechos de matrícula. 3. Carga de documentos requeridos. 4. Inscripción de asignaturas. Te recomendamos visitar la sección de 'Admisiones' en nuestra página web para ver la guía detallada y fechas.",
            "category": "Académico - Matrículas"
        }
    logger.info(f"API_CLIENT_CUL (Simulación): No se encontró FAQ simulada para '{query}'")
    return {"info_consulta": "No encontré una respuesta directa en nuestra base de conocimiento para esa pregunta específica."}

# Necesario importar asyncio si no está ya en el archivo
import asyncio
