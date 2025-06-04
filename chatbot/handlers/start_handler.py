# chatbot/handlers/start_handler.py
# MODIFICADO PARA EL CHATBOT UNIVERSITARIO CUL

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler 
from telegram.constants import ParseMode
from chatbot.bot_logging import logger
# Importar el punto de entrada del ConversationHandler de tickets
from .ticket_handler import start_ticket_creation # Importante

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    logger.info(f"Usuario {user.id} ({user.username or user.first_name}) inició el bot CUL con /start o /ayuda.")
    
    welcome_message = (
        f"¡Hola, {user.first_name}! 👋\n\n"
        "Soy <b>Asistente CUL</b>, tu guía virtual en la Corporación Universitaria Latinoamericana.\n\n"
        "Estoy aquí para ayudarte con:\n"
        "📚 Información sobre trámites académicos.\n"
        "📅 Horarios y calendario académico.\n"
        "💻 Soporte técnico básico (plataformas, correo, Wi-Fi).\n"
        "🏛️ Consultas generales sobre la universidad.\n\n"
        "<b>Comandos útiles:</b>\n"
        "🆘 /ayuda - Muestra este mensaje.\n"
        "🎫 /ticket - Para crear una solicitud de soporte detallada.\n" # Actualizado
        "🔄 /reset_chat - Reinicia nuestra conversación.\n\n"
        "Puedes escribirme tu consulta directamente en lenguaje natural. Por ejemplo: <i>\"¿Cuáles son los requisitos para la inscripción?\"</i> o <i>\"No puedo acceder a la plataforma de notas\"</i>.\n\n"
        "¿Cómo puedo colaborarte hoy?"
    )
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)

# El comando /ticket ahora es un entry_point del ConversationHandler en ticket_handler.py
# por lo que no necesitamos una función ticket_command separada aquí si se registra
# directamente el ConversationHandler para el comando /ticket.
# Si quisiéramos hacer algo ANTES de entrar al ConversationHandler,
# podríamos tener una función aquí y que ella retorne el primer estado del ConvHandler.
# Por simplicidad, lo dejaremos como entry_point directo.

# async def ticket_command_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Función que podría usarse si se quiere pre-procesar algo antes de llamar a start_ticket_creation."""
#     # ... lógica de pre-procesamiento ...
#     return await start_ticket_creation(update, context)
