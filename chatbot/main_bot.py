# Archivo: chatbot/main_bot.py
# Punto de entrada principal para configurar e iniciar el bot de Telegram.
# MODIFICADO PARA EL CHATBOT UNIVERSITARIO CUL (con ConversationHandler para tickets)

import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler # Necesario para el ConversationHandler de tickets
)

from chatbot.config import TELEGRAM_BOT_TOKEN, LOG_LEVEL
from chatbot.bot_logging import logger, setup_logging

# Importar handlers actualizados/nuevos
from chatbot.handlers import start_handler
from chatbot.handlers.general_handler import general_message_handler, reset_chat_command
# Importar el ConversationHandler de tickets
from chatbot.handlers.ticket_handler import ticket_creation_conv_handler


def main() -> None:
    setup_logging(level_name=LOG_LEVEL)
    logger.info("============================================================")
    logger.info("🚀 INICIANDO BOT ASISTENTE CUL (UNIVERSITARIO) v2 🚀")
    logger.info("============================================================")

    if not TELEGRAM_BOT_TOKEN:
        logger.critical("CRÍTICO: TELEGRAM_BOT_TOKEN no encontrado. El bot CUL no puede iniciar.")
        return

    application_builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    application_builder.read_timeout(30)
    application_builder.write_timeout(30)
    application_builder.connect_timeout(30)
    application = application_builder.build()
    
    async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(msg="EXCEPCIÓN NO MANEJADA AL PROCESAR UN UPDATE (CUL):", exc_info=context.error)
        if isinstance(update, Update) and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🚧 ¡Ups! Parece que encontré un inconveniente técnico (error inesperado) al procesar tu solicitud. 🚧\n"
                         "El equipo de la CUL ha sido notificado (simulado). Por favor, intenta de nuevo en unos momentos."
                )
            except Exception as e_notify:
                logger.error(f"Error al intentar enviar mensaje de error CUL al usuario {update.effective_chat.id}: {e_notify}")
    application.add_error_handler(global_error_handler)

    logger.info("Registrando handlers para el Bot CUL...")

    # Handlers principales
    application.add_handler(CommandHandler(["start", "ayuda"], start_handler.start))
    logger.debug("Handler para /start, /ayuda (CUL) registrado.")

    application.add_handler(CommandHandler("reset_chat", reset_chat_command))
    logger.debug("Handler para /reset_chat (CUL) registrado.")
    
    # Registrar el ConversationHandler para la creación de tickets
    # Debe ir ANTES del general_message_handler si sus entry_points son comandos.
    # Si tuviera entry_points de MessageHandler, el orden y los filtros serían más críticos.
    application.add_handler(ticket_creation_conv_handler)
    logger.debug("ConversationHandler para creación de tickets (CUL) registrado.")

    # El general_message_handler debe ir después de los CommandHandlers y ConversationHandlers
    # para que no capture los comandos o mensajes destinados a las conversaciones.
    application.add_handler(general_message_handler)
    logger.debug("MessageHandler general para texto (LLM CUL) registrado.")


    async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and update.message.text and update.message.text.startswith('/'):
            # Verificar si el comando es parte de una conversación activa
            # Esto es un poco más complejo, ConversationHandler maneja esto internamente.
            # Si no está en una conversación, entonces es realmente desconocido.
            current_handlers = context.application.handlers
            # Esta verificación es superficial, PTB maneja la prioridad de handlers.
            # Si llega aquí, es porque ningún CommandHandler específico lo tomó.
            logger.warning(f"Comando CUL desconocido: {update.message.text} de user_id {update.effective_user.id if update.effective_user else 'N/A'}")
            await update.message.reply_text(
                "🤔 Lo siento, no reconozco ese comando.\n"
                "Puedes usar /ayuda para ver las opciones disponibles o /ticket para crear una solicitud."
            )
    # Registrar el handler para comandos desconocidos.
    # El grupo 1 asegura que se ejecute después de los handlers del grupo 0 (por defecto).
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler), group=1)
    logger.debug("Handler para comandos desconocidos (CUL) registrado.")
    
    logger.info("🤖 Bot CUL configurado y listo. Iniciando polling...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
    except KeyboardInterrupt:
        logger.info("Polling CUL detenido manualmente (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"El bot CUL se detuvo por error crítico no manejado en polling: {e}", exc_info=True)
    finally:
        logger.info("============================================================")
        logger.info("🛑 BOT CUL DETENIDO 🛑")
        logger.info("============================================================")

if __name__ == "__main__":
    main()
