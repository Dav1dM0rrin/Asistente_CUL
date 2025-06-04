# Archivo: chatbot/handlers/conversation_states.py
# Define las constantes para los estados de los ConversationHandlers.
# MODIFICADO PARA EL CHATBOT UNIVERSITARIO CUL

# --- Estados para el Flujo de Creación de Tickets ---
# Estos estados guiarán la conversación para recolectar información para un ticket.

(
    ASK_TICKET_DESCRIPTION,         # 0: Preguntar/confirmar descripción del problema
    ASK_TICKET_CATEGORY,            # 1: Preguntar la categoría del problema (con opciones)
    ASK_TICKET_EMAIL,               # 2: Preguntar el correo electrónico de contacto
    ASK_TICKET_STUDENT_ID,          # 3: Preguntar ID de estudiante/documento (opcional)
    CONFIRM_TICKET_CREATION,        # 4: Mostrar resumen y pedir confirmación final
    HANDLE_TICKET_API_RESPONSE      # 5: (Interno) Paso después de llamar a la API, no es un estado de espera de usuario
) = range(6) # Asegúrate de que el rango cubra todos los estados definidos

# Estados para el Flujo de Reporte de Accidentes (Eliminados)
# ...

# Otros estados que puedas necesitar en el futuro
# ...
