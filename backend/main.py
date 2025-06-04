# main.py (API para Chatbot CUL)

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

# Importar modelos y funciones crud (simuladas)
from crud import crud
from models import models

# --- Metadata para la documentación de la API (Swagger UI / ReDoc) ---
API_TITLE = "API para Chatbot CUL"
API_VERSION = "0.1.0"
API_DESCRIPTION = """
API para gestionar la creación de tickets de soporte y la consulta de Preguntas Frecuentes (FAQs)
para el chatbot de la Corporación Universitaria Latinoamericana (CUL).
"""

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    # openapi_url="/api/cul/v1/openapi.json", # Estructura de URL sugerida
    # docs_url="/api/cul/v1/docs",
    # redoc_url="/api/cul/v1/redoc"
)

# --- Configuración de CORS (Cross-Origin Resource Sharing) ---
# Permite que tu chatbot (si se ejecuta desde un origen diferente) interactúe con la API.
# Para desarrollo, puedes usar orígenes más permisivos. Para producción, sé específico.
origins = [
    "http://localhost", # Si el chatbot corre localmente
    "http://localhost:8080", # Ejemplo si tienes un frontend de prueba
    # "*" # Permisivo, no recomendado para producción sin entender implicaciones
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"], # Métodos HTTP permitidos
    allow_headers=["*"], # Cabeceras permitidas
)

# --- Endpoints de la API ---

@app.get("/api/cul/v1/", response_model=models.HealthCheck, tags=["General"])
async def root():
    """
    Endpoint raíz para verificar el estado de la API.
    """
    return {"status": "OK", "message": f"{API_TITLE} v{API_VERSION} está operativa."}

# --- Endpoints para Tickets ---
@app.post("/api/cul/v1/tickets/",
            response_model=models.TicketResponse,
            status_code=201, # HTTP 201 Created
            summary="Crear un nuevo ticket de soporte",
            tags=["Tickets"])
async def create_new_ticket(ticket_data: models.TicketCreate = Body(...)):
    """
    Crea un nuevo ticket de soporte con la información proporcionada.

    - **user_id_telegram**: ID del usuario en Telegram (opcional).
    - **user_name_telegram**: Nombre del usuario en Telegram (opcional).
    - **user_email**: Email de contacto del usuario (opcional pero recomendado).
    - **problem_description**: Descripción detallada del problema o consulta.
    - **category**: Categoría del ticket (ej: "Soporte Técnico", "Admisiones", "Académico").
    - **priority**: Prioridad del ticket (ej: "Alta", "Media", "Baja").
    - **source**: Origen del ticket (ej: "Chatbot CUL Telegram").
    """
    try:
        created_ticket = await crud.create_ticket_in_db(ticket_data)
        return created_ticket
    except ValueError as e: # Ejemplo de manejo de error de validación
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # En un entorno de producción, loguear el error `e`
        print(f"Error inesperado al crear ticket: {e}") # Log a consola para debug
        raise HTTPException(status_code=500, detail="Error interno del servidor al procesar el ticket.")

@app.get("/api/cul/v1/tickets/{ticket_id}",
           response_model=models.TicketResponse,
           summary="Obtener un ticket por su ID",
           tags=["Tickets"])
async def get_ticket_by_id(ticket_id: str):
    """
    Obtiene los detalles de un ticket específico utilizando su ID.
    """
    ticket = await crud.get_ticket_from_db(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket con ID '{ticket_id}' no encontrado.")
    return ticket

@app.get("/api/cul/v1/tickets/",
            response_model=List[models.TicketResponse],
            summary="Listar todos los tickets (con filtros opcionales)",
            tags=["Tickets"])
async def list_all_tickets(
    status: Optional[str] = Query(None, description="Filtrar tickets por estado (ej: 'Abierto', 'Cerrado')"),
    category: Optional[str] = Query(None, description="Filtrar tickets por categoría"),
    user_id_telegram: Optional[str] = Query(None, description="Filtrar tickets por ID de usuario de Telegram")
):
    """
    Obtiene una lista de todos los tickets, con posibilidad de aplicar filtros.
    (Simulación: los filtros no están completamente implementados en el CRUD simulado)
    """
    filters_dict = {}
    if status:
        filters_dict["status"] = status
    if category:
        filters_dict["category"] = category
    if user_id_telegram:
        filters_dict["user_id_telegram"] = user_id_telegram
        
    tickets = await crud.get_all_tickets_from_db(filters=filters_dict)
    return tickets

# --- Endpoints para FAQs ---
@app.get("/api/cul/v1/faqs/",
           response_model=List[models.FAQResponse],
           summary="Buscar o listar FAQs",
           tags=["FAQs"])
async def search_faqs(
    query: Optional[str] = Query(None, description="Término de búsqueda para preguntas o respuestas de FAQs."),
    category: Optional[str] = Query(None, description="Filtrar FAQs por categoría (ej: 'Matrículas', 'Soporte Técnico').")
):
    """
    Busca FAQs que coincidan con el término de búsqueda y/o categoría.
    Si no se proporcionan parámetros, devuelve todas las FAQs (limitado en simulación).
    """
    faqs = await crud.get_faqs_from_db(query_term=query, category_filter=category)
    if not faqs and (query or category): # Si hubo búsqueda pero no resultados
        # Podrías devolver 200 con lista vacía o 404 si es mandatorio encontrar algo.
        # Devolver 200 con lista vacía es común para búsquedas.
        return []
    return faqs

@app.post("/api/cul/v1/faqs/",
            response_model=models.FAQResponse,
            status_code=201,
            summary="Crear una nueva FAQ (para administradores)",
            tags=["FAQs"])
async def create_new_faq(faq_data: models.FAQCreate = Body(...)):
    """
    Crea una nueva Pregunta Frecuente en el sistema.
    (Este endpoint sería típicamente protegido y solo para administradores)
    """
    created_faq = await crud.create_faq_in_db(faq_data)
    return created_faq

# --- Para ejecutar la API directamente con Uvicorn (para desarrollo) ---
if __name__ == "__main__":
    import uvicorn
    # La estructura de directorios para `from . import models` requiere ejecutar como módulo:
    # python -m api_cul.main  (si tu directorio se llama api_cul)
    # O ajustar imports si `main.py` está en la raíz del proyecto de API.
    # Para simplificar, si este `main.py` está en la raíz de su propio proyecto de API:
    # from models import TicketCreate, FAQCreate # etc.
    # from crud import create_ticket_in_db # etc.
    
    print("Para ejecutar esta API, usa: uvicorn main:app --reload")
    print("Por ejemplo, si este archivo es 'main.py' en el directorio 'api_cul_project',")
    print("navega a 'api_cul_project' y ejecuta 'uvicorn main:app --reload'.")
    print("La API estará disponible en http://127.0.0.1:8000")
    # uvicorn.run(app, host="0.0.0.0", port=8000) # Esto no funciona bien con --reload desde el script
