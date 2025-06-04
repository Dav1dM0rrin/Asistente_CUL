# models.py (API para Chatbot CUL)

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid

# --- Modelos para Tickets ---

class TicketBase(BaseModel):
    """Modelo base para los datos de un ticket."""
    user_id_telegram: Optional[str] = Field(None, description="ID del usuario en Telegram")
    user_name_telegram: Optional[str] = Field(None, description="Nombre del usuario en Telegram")
    user_email: Optional[EmailStr] = Field(None, description="Email de contacto del usuario")
    problem_description: str = Field(..., min_length=10, description="Descripción detallada del problema o consulta")
    category: Optional[str] = Field("General", description="Categoría del ticket (ej: Soporte Técnico, Admisiones)")
    priority: Optional[str] = Field("Media", description="Prioridad del ticket (ej: Alta, Media, Baja)")
    source: Optional[str] = Field("Desconocido", description="Origen del ticket (ej: Chatbot CUL Telegram)")

class TicketCreate(TicketBase):
    """Modelo para la creación de un nuevo ticket."""
    pass # Hereda todos los campos de TicketBase

class TicketResponse(TicketBase):
    """Modelo para la respuesta al obtener o crear un ticket."""
    id: str = Field(..., description="ID único del ticket generado por el sistema")
    status: str = Field("Abierto", description="Estado actual del ticket (ej: Abierto, En Proceso, Cerrado)")
    created_at: datetime = Field(..., description="Fecha y hora de creación del ticket (UTC)")
    updated_at: Optional[datetime] = Field(None, description="Fecha y hora de la última actualización (UTC)")

    class Config:
        orm_mode = True # Para compatibilidad si usaras un ORM como SQLAlchemy
        # Pydantic V2 usa `from_attributes = True` en lugar de `orm_mode = True`
        # from_attributes = True 

# --- Modelos para FAQs ---

class FAQBase(BaseModel):
    """Modelo base para una Pregunta Frecuente."""
    question: str = Field(..., min_length=5, description="La pregunta frecuente")
    answer: str = Field(..., min_length=10, description="La respuesta a la pregunta")
    category: Optional[str] = Field("General", description="Categoría de la FAQ (ej: Matrículas, Bienestar)")
    keywords: Optional[List[str]] = Field([], description="Palabras clave para búsqueda")

class FAQCreate(FAQBase):
    """Modelo para la creación de una nueva FAQ."""
    pass

class FAQResponse(FAQBase):
    """Modelo para la respuesta al obtener una FAQ."""
    id: str = Field(..., description="ID único de la FAQ")
    created_at: datetime = Field(..., description="Fecha y hora de creación de la FAQ (UTC)")
    updated_at: Optional[datetime] = Field(None, description="Fecha y hora de la última actualización (UTC)")
    # relevance_score: Optional[float] = Field(None, description="Puntuación de relevancia si es resultado de una búsqueda") # Ejemplo

    class Config:
        orm_mode = True
        # from_attributes = True

# --- Modelo para Health Check ---
class HealthCheck(BaseModel):
    status: str
    message: str
