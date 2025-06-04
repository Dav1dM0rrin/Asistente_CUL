# Archivo: chatbot/handlers/general_handler.py
# Maneja mensajes de texto generales, interactuando con el servicio LLM.
# MODIFICADO PARA EL CHATBOT UNIVERSITARIO CUL (para integrarse con ticket_handler)

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler
from telegram.constants import ChatAction

from chatbot.llm_service import (
    generate_response,
    classify_intent_and_extract_entities,
    reset_conversation_history
)
from chatbot.bot_logging import logger
from chatbot.api_client import get_faq_from_api # create_ticket_api se usará en ticket_handler
# Importar el punto de entrada del ConversationHandler de tickets y sus estados
from .ticket_handler import start_ticket_creation 
from .conversation_states import ASK_TICKET_DESCRIPTION # Para iniciar el flujo

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None: # Puede devolver un estado
    if not update.message or not update.message.text:
        logger.debug("GENERAL_HANDLER_CUL: Mensaje vacío o sin texto recibido, ignorando.")
        return

    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name or update.effective_user.username
    user_message = update.message.text.strip()

    if not user_message:
        logger.debug(f"GENERAL_HANDLER_CUL: Mensaje de user_id {user_id} vacío tras strip, ignorando.")
        return

    logger.info(f"GENERAL_HANDLER_CUL: Mensaje de user_id {user_id} ({user_name}): '{user_message}'")
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # Ya no manejamos 'pending_action' aquí para tickets, se delega al ConversationHandler

        # 1. Clasificación de Intención y Extracción de Entidades
        classification_result = await classify_intent_and_extract_entities(user_message)
        intent = classification_result.get("intent", "DESCONOCIDO")
        entities = classification_result.get("entities", {})
        
        logger.info(f"GENERAL_HANDLER_CUL: Intención clasificada para '{user_message}': {intent}. Entidades: {entities}")
        if classification_result.get("error"):
            logger.warning(f"GENERAL_HANDLER_CUL: Error en clasificación: {classification_result.get('error')}. Se usará LLM general.")

        api_data_for_llm = None

        # 2. Lógica RAG (FAQs) o Inicio de Flujo de Ticket
        if intent == "GENERAR_TICKET_HUMANO" and not classification_result.get("error"):
            logger.info(f"GENERAL_HANDLER_CUL: Intención GENERAR_TICKET_HUMANO detectada para user_id {user_id}.")
            resumen_solicitud = entities.get("resumen_solicitud_ticket", user_message)
            
            # Guardar la descripción inicial si el LLM la extrajo, para que ticket_handler la use
            if resumen_solicitud:
                context.user_data['llm_ticket_initial_description'] = resumen_solicitud
            
            # Iniciar el ConversationHandler de creación de tickets
            # Esto es un poco "hacky" porque un MessageHandler normalmente no devuelve un estado
            # para OTRO ConversationHandler. Una mejor forma sería que el main_bot.py
            # tenga un entry_point para el ticket_creation_conv_handler que sea un MessageHandler
            # que filtre por esta intención (requeriría una función de filtro personalizada).
            # Por ahora, llamaremos directamente a la función de inicio del otro handler.
            # ¡ESTO NO FUNCIONARÁ ASÍ DIRECTAMENTE! Un MessageHandler no puede simplemente
            # pasar el control a un estado de un ConversationHandler que no lo llamó.

            # Corrección: En lugar de llamar a start_ticket_creation directamente,
            # el LLM debería simplemente sugerir al usuario usar /ticket o responder de forma que
            # el usuario naturalmente provea la descripción.
            # O, si queremos que el LLM inicie el flujo, el LLM debe responder con un mensaje
            # y el *siguiente* mensaje del usuario sería capturado por el ticket_handler.
            #
            # Para una integración más fluida:
            # El LLM podría responder: "Entendido, parece que necesitas ayuda. Para crear un ticket,
            # por favor dime primero una breve descripción del problema."
            # Y el ConversationHandler de tickets tendría un entry point que es un MessageHandler
            # esperando esta descripción.

            # Simplificación por ahora: El LLM informará y el usuario usará /ticket.
            # O, si el LLM es muy bueno, podría guiarlo y luego nosotros extraeríamos los datos.
            # La forma más robusta es que el LLM sugiera el comando /ticket.

            # Si el LLM detecta la intención de crear un ticket, puede responder:
            # "Entendido, parece que necesitas asistencia. Puedes iniciar la creación de un ticket usando el comando /ticket."
            # Y luego el ConversationHandler se activará con ese comando.
            # Por ahora, dejaremos que el LLM responda y el usuario use /ticket.
            # Si el usuario ya dio una descripción, el LLM puede decir:
            # "Entendido. Para tu problema: '{resumen_solicitud}', te recomiendo crear un ticket. Usa /ticket para continuar."
            # El `general_message_handler` NO iniciará el `ticket_creation_conv_handler`.
            # El `ticket_creation_conv_handler` se inicia con `/ticket`.

            # Si el LLM detecta la intención y ya hay una descripción, podría guardarla
            # para que el `/ticket` la recoja.
            if resumen_solicitud:
                 context.user_data['llm_ticket_initial_description'] = resumen_solicitud
                 logger.info(f"GENERAL_HANDLER_CUL: Descripción '{resumen_solicitud}' guardada para posible uso con /ticket.")


        consult_intents = ["CONSULTA_TRAMITE_ACADEMICO", "CONSULTA_HORARIO", "CONSULTA_PROGRAMA_ACADEMICO", "INFORMACION_GENERAL_CUL"]
        if intent in consult_intents and not classification_result.get("error"):
            logger.info(f"GENERAL_HANDLER_CUL: Intención de consulta '{intent}'. Buscando en FAQs para: '{user_message}'")
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            
            faq_query = user_message
            faq_subject = entities.get("nombre_tramite") or \
                          entities.get("nombre_asignatura") or \
                          entities.get("nombre_programa") or \
                          entities.get("tema_consulta_general")

            api_faq_response = await get_faq_from_api(query=faq_query, subject=faq_subject)
            
            if api_faq_response and api_faq_response.get("answer"):
                logger.info(f"GENERAL_HANDLER_CUL: FAQ encontrada para '{user_message}'. ID: {api_faq_response.get('faq_id')}")
                api_data_for_llm = {"faq_encontrada": api_faq_response}
            elif isinstance(api_faq_response, dict) and api_faq_response.get("info_consulta"):
                 logger.info(f"GENERAL_HANDLER_CUL: API de FAQ respondió: {api_faq_response.get('info_consulta')}")

        # 3. Generación de Respuesta con LLM
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        final_llm_response_text = await generate_response(
            user_id,
            user_message, # El mensaje original del usuario
            api_data_context=api_data_for_llm
        )
        
        if final_llm_response_text and final_llm_response_text.strip():
            await update.message.reply_text(final_llm_response_text)
        else:
            logger.error(f"GENERAL_HANDLER_CUL: LLM no generó respuesta para '{user_message}' de {user_id}.")
        return None # No devuelve estado de conversación

    except Exception as e:
        logger.error(f"GENERAL_HANDLER_CUL: Excepción en handle_message para '{user_message}' de {user_id}: {e}", exc_info=True)
        try:
            await update.message.reply_text("Lo siento, tuve un inconveniente técnico al procesar tu solicitud. Por favor, intenta de nuevo en un momento.")
        except Exception as e_reply:
            logger.error(f"GENERAL_HANDLER_CUL: No se pudo enviar mensaje de error a {user_id}: {e_reply}", exc_info=True)
        return None # No devuelve estado de conversación
    
    logger.info(f"GENERAL_HANDLER_CUL: Fin handle_message para user_id {user_id}.")


async def reset_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        logger.warning("RESET_CHAT_CUL: No se pudo obtener effective_user.")
        return

    user_id = str(update.effective_user.id)
    logger.info(f"RESET_CHAT_CUL: Comando /reset_chat de user_id {user_id}.")

    if await reset_conversation_history(user_id):
        await update.message.reply_text(
            "He reseteado nuestro historial de conversación. 🧠✨\n"
            "¡Empecemos de nuevo! ¿En qué te puedo ayudar sobre la CUL?"
        )
    else:
        await update.message.reply_text(
            "No había un historial previo que resetear, ¡así que estamos listos! 😊\n"
            "¿Cómo te puedo asistir?"
        )

general_message_handler = MessageHandler(
    filters.UpdateType.MESSAGE & filters.TEXT & ~filters.COMMAND,
    handle_message
)
