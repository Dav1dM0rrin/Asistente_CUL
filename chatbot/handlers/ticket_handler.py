# Archivo: chatbot/handlers/ticket_handler.py
# Maneja el flujo de conversación para la creación de tickets de soporte.

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from chatbot.bot_logging import logger
from chatbot.api_client import create_ticket_api
from .conversation_states import (
    ASK_TICKET_DESCRIPTION,
    ASK_TICKET_CATEGORY,
    ASK_TICKET_EMAIL,
    ASK_TICKET_STUDENT_ID,
    CONFIRM_TICKET_CREATION
)
import re # Para validación de email

# --- Opciones para Categorías de Tickets ---
TICKET_CATEGORIES = [
    "Soporte Técnico (Plataformas, Correo, WiFi)",
    "Consultas Académicas (Trámites, Horarios, Programas)",
    "Admisiones y Matrículas",
    "Bienestar Universitario",
    "Pagos y Cartera",
    "Biblioteca",
    "Otro"
]

# --- Funciones del ConversationHandler para Tickets ---

async def start_ticket_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Punto de entrada para el flujo de creación de tickets.
    Puede ser llamado por el comando /ticket o por el LLM.
    """
    user = update.effective_user
    logger.info(f"TICKET_HANDLER: Usuario {user.id} ({user.full_name or user.username}) inició creación de ticket.")
    
    context.user_data['current_ticket_data'] = {} # Limpiar/iniciar datos para este ticket

    # Verificar si el LLM ya extrajo una descripción (desde general_handler)
    pre_extracted_description = context.user_data.pop('llm_ticket_initial_description', None)

    if pre_extracted_description:
        logger.info(f"TICKET_HANDLER: Usando descripción pre-extraída por LLM: '{pre_extracted_description}'")
        context.user_data['current_ticket_data']['problem_description'] = pre_extracted_description
        await update.message.reply_text(
            f"Entendido. Has mencionado: \"<i>{pre_extracted_description}</i>\"\n\n"
            "Si esa es la descripción correcta, continuemos. Si no, puedes corregirla ahora o cancelarla con /cancelar_ticket.",
            parse_mode='HTML'
        )
        # Avanzamos directamente a pedir la categoría si ya tenemos descripción
        return await ask_ticket_category(update, context, from_pre_description=True)
    else:
        await update.message.reply_text(
            "¡Claro! Vamos a crear un ticket de soporte.\n\n"
            "Por favor, describe brevemente el problema o la consulta que tienes:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_TICKET_DESCRIPTION

async def get_ticket_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda la descripción del problema y pregunta la categoría."""
    description = update.message.text.strip()
    if not description or len(description) < 10:
        await update.message.reply_text(
            "Por favor, proporciona una descripción un poco más detallada (mínimo 10 caracteres) para que podamos ayudarte mejor."
        )
        return ASK_TICKET_DESCRIPTION

    context.user_data['current_ticket_data']['problem_description'] = description
    logger.info(f"TICKET_HANDLER: Descripción del ticket: '{description}'")
    
    return await ask_ticket_category(update, context)

async def ask_ticket_category(update: Update, context: ContextTypes.DEFAULT_TYPE, from_pre_description: bool = False) -> int:
    """Pregunta la categoría del ticket."""
    category_keyboard = [[KeyboardButton(cat)] for cat in TICKET_CATEGORIES]
    
    message_text = "Descripción registrada." if not from_pre_description else ""
    message_text += "\n\nAhora, por favor, selecciona la categoría que mejor se ajusta a tu solicitud:"

    await update.message.reply_text(
        message_text,
        reply_markup=ReplyKeyboardMarkup(category_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_TICKET_CATEGORY

async def get_ticket_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda la categoría y pregunta el email."""
    category = update.message.text.strip()
    if category not in TICKET_CATEGORIES:
        await update.message.reply_text(
            "Por favor, selecciona una categoría válida de la lista proporcionada."
        )
        # Re-mostrar teclado de categorías
        category_keyboard = [[KeyboardButton(cat)] for cat in TICKET_CATEGORIES]
        await update.message.reply_text(
            "Selecciona la categoría:",
            reply_markup=ReplyKeyboardMarkup(category_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return ASK_TICKET_CATEGORY

    context.user_data['current_ticket_data']['category'] = category
    logger.info(f"TICKET_HANDLER: Categoría del ticket: '{category}'")
    
    await update.message.reply_text(
        "Categoría registrada.\n\n"
        "Ahora, por favor, indícame tu dirección de correo electrónico para que podamos contactarte:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_TICKET_EMAIL

async def get_ticket_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda el email y pregunta el ID de estudiante (opcional)."""
    email = update.message.text.strip()
    # Validación simple de email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text(
            "La dirección de correo electrónico no parece válida. Por favor, ingrésala de nuevo (ej: usuario@dominio.com)."
        )
        return ASK_TICKET_EMAIL

    context.user_data['current_ticket_data']['user_email'] = email
    logger.info(f"TICKET_HANDLER: Email del ticket: '{email}'")

    # Teclado para ID de estudiante (opcional)
    student_id_keyboard = [["Omitir este paso"]]
    await update.message.reply_text(
        "Correo electrónico registrado.\n\n"
        "Si eres estudiante y lo tienes a mano, por favor, proporciona tu número de identificación estudiantil o documento de identidad. "
        "Si no aplica o no lo tienes, puedes 'Omitir este paso'.",
        reply_markup=ReplyKeyboardMarkup(student_id_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_TICKET_STUDENT_ID

async def get_ticket_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda el ID de estudiante (si se proporciona) y muestra el resumen para confirmación."""
    student_id_input = update.message.text.strip()

    if student_id_input.lower() == "omitir este paso":
        context.user_data['current_ticket_data']['student_id'] = None
        logger.info("TICKET_HANDLER: ID de estudiante omitido.")
    else:
        # Podrías añadir una validación más específica para el formato del ID si es necesario
        context.user_data['current_ticket_data']['student_id'] = student_id_input
        logger.info(f"TICKET_HANDLER: ID de estudiante/documento: '{student_id_input}'")
    
    return await show_ticket_summary_and_confirm(update, context)

async def show_ticket_summary_and_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra un resumen de los datos del ticket y pide confirmación."""
    ticket_data = context.user_data.get('current_ticket_data', {})
    
    summary_parts = [
        "📝 *Resumen de tu Solicitud de Soporte*",
        "Por favor, verifica que la información sea correcta antes de enviar:\n",
        f"*Descripción*: {ticket_data.get('problem_description', 'No especificada')}",
        f"*Categoría*: {ticket_data.get('category', 'No especificada')}",
        f"*Correo de Contacto*: {ticket_data.get('user_email', 'No especificado')}",
    ]
    if ticket_data.get('student_id'):
        summary_parts.append(f"*ID Estudiante/Documento*: {ticket_data.get('student_id')}")
    else:
        summary_parts.append("*ID Estudiante/Documento*: Omitido")
    
    summary_parts.append("\n¿Deseas enviar este ticket?")

    confirmation_keyboard = [["✅ Sí, enviar ticket"], ["❌ No, cancelar"]]
    await update.message.reply_text(
        "\n".join(summary_parts),
        reply_markup=ReplyKeyboardMarkup(confirmation_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return CONFIRM_TICKET_CREATION

async def process_ticket_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa la confirmación final y envía el ticket a la API."""
    user_choice = update.message.text
    user = update.effective_user

    if "✅ Sí, enviar ticket" not in user_choice:
        await update.message.reply_text("Creación de ticket cancelada.", reply_markup=ReplyKeyboardRemove())
        context.user_data.pop('current_ticket_data', None)
        return ConversationHandler.END

    ticket_data_collected = context.user_data.get('current_ticket_data', {})
    
    # Preparar payload para la API
    api_payload = {
        "user_id_telegram": str(user.id),
        "user_name_telegram": user.full_name or user.username,
        "user_email": ticket_data_collected.get('user_email'),
        "problem_description": ticket_data_collected.get('problem_description'),
        "category": ticket_data_collected.get('category'),
        # "student_id": ticket_data_collected.get('student_id'), # La API actual no tiene este campo, añadir si es necesario
        "source": "Chatbot CUL Telegram",
        "priority": "Media" # Podrías determinar la prioridad basado en la categoría o descripción
    }
    # Si tu API espera student_id, asegúrate de que el modelo Pydantic en la API lo incluya.
    # Por ahora, lo omito del payload principal si la API no lo espera.

    logger.info(f"TICKET_HANDLER: Enviando payload de ticket a la API: {api_payload}")
    await update.message.reply_text("Procesando tu solicitud de ticket...", reply_markup=ReplyKeyboardRemove())
    
    api_response = await create_ticket_api(api_payload)

    if api_response and api_response.get("success"): # Asumiendo que tu API devuelve 'success': True
        ticket_id_api = api_response.get("ticket_id", "N/A")
        message_api = api_response.get("message", "Un asesor se pondrá en contacto contigo pronto.")
        success_msg = (f"¡Ticket enviado con éxito! 👍\n"
                       f"Tu número de ticket es: <b>{ticket_id_api}</b>\n"
                       f"{message_api}\n\n"
                       "¿Hay algo más en lo que pueda ayudarte?")
        await update.message.reply_text(success_msg, parse_mode='HTML')
    else:
        error_detail = "No se pudo procesar el ticket en el servidor."
        if isinstance(api_response, dict) and api_response.get("detail"):
            error_detail = api_response.get("detail")
        elif isinstance(api_response, dict) and api_response.get("error"):
             error_detail = str(api_response.get("error"))

        await update.message.reply_text(f"Hubo un problema al enviar tu ticket: <i>{error_detail}</i>\nPor favor, intenta de nuevo más tarde o contacta directamente a la universidad.")
        logger.error(f"TICKET_HANDLER: Error al enviar ticket a API. Payload: {api_payload}. Respuesta API: {api_response}")

    context.user_data.pop('current_ticket_data', None)
    return ConversationHandler.END

async def cancel_ticket_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela el flujo de creación de ticket."""
    await update.message.reply_text("Creación de ticket cancelada.", reply_markup=ReplyKeyboardRemove())
    context.user_data.pop('current_ticket_data', None)
    return ConversationHandler.END

# --- Definición del ConversationHandler ---
ticket_creation_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("ticket", start_ticket_creation),
        # Podríamos añadir un MessageHandler aquí si el LLM detecta la intención
        # y pasa un flag para iniciar este flujo.
    ],
    states={
        ASK_TICKET_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket_description)],
        ASK_TICKET_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket_category)],
        ASK_TICKET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket_email)],
        ASK_TICKET_STUDENT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket_student_id)],
        CONFIRM_TICKET_CREATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ticket_confirmation)],
    },
    fallbacks=[
        CommandHandler("cancelar_ticket", cancel_ticket_creation),
        CommandHandler("start", cancel_ticket_creation), # Cancelar si se inicia otro comando principal
        CommandHandler("ayuda", cancel_ticket_creation)
    ],
    map_to_parent={ # Si este ConvHandler es anidado, cómo volver al padre
        ConversationHandler.END: ConversationHandler.END 
    },
    # per_user=True, per_chat=True, per_message=False # Configuración de persistencia de estado
    # allow_reentry=True # Permitir reingresar al handler con el mismo comando
)
