# api_cul_project/crud.py
# Operaciones CRUD interactuando con la base de datos MySQL.

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone # timezone no es necesario para pymysql directamente
import uuid
import pymysql # Para manejar errores específicos de pymysql

# Importar modelos Pydantic y configuración de BD
from models import models
from core.database import get_db_connection

# --- Funciones CRUD para Tickets ---

async def create_ticket_in_db(ticket_data: models.TicketCreate) -> models.TicketResponse:
    """Crea un nuevo ticket en la base de datos."""
    ticket_id = str(uuid.uuid4())
    # Nota: created_at y updated_at son manejados por la BD (DEFAULT CURRENT_TIMESTAMP)
    # El status también tiene un DEFAULT 'Abierto' en la BD.

    sql = """
    INSERT INTO tickets (id, user_id_telegram, user_name_telegram, user_email, 
                         problem_description, category, priority, source, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    # El estado 'Abierto' se puede pasar explícitamente o confiar en el DEFAULT de la BD
    args = (
        ticket_id,
        ticket_data.user_id_telegram,
        ticket_data.user_name_telegram,
        ticket_data.user_email,
        ticket_data.problem_description,
        ticket_data.category,
        ticket_data.priority,
        ticket_data.source,
        "Abierto" # Estado inicial explícito
    )

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
        conn.commit()
        
        # Para devolver el objeto completo, necesitamos recuperarlo o construirlo
        # La BD ya tiene created_at, updated_at, status.
        # Vamos a recuperarlo para ser precisos
        created_ticket = await get_ticket_from_db(ticket_id)
        if not created_ticket: # Esto no debería pasar si la inserción fue exitosa
             raise Exception("Ticket creado pero no pudo ser recuperado.")
        print(f"CRUD: Ticket creado con ID {ticket_id} en la BD.")
        return created_ticket
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al crear ticket: {e}")
        # Podrías querer deshacer (rollback) si algo falla, aunque commit es al final.
        # if conn: conn.rollback() # No es necesario aquí si el error es antes del commit
        raise HTTPException(status_code=500, detail=f"Error de base de datos al crear ticket: {e}")
    except Exception as e:
        print(f"CRUD Error (General) al crear ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado al crear ticket: {e}")
    finally:
        if conn:
            conn.close()

async def get_ticket_from_db(ticket_id: str) -> Optional[models.TicketResponse]:
    """Obtiene un ticket de la base de datos por su ID."""
    sql = "SELECT * FROM tickets WHERE id = %s"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, (ticket_id,))
            result = cursor.fetchone() # fetchone() devuelve un dict gracias a DictCursor
        
        if result:
            # Convertir las fechas de la BD (objetos datetime) a cadenas ISO si es necesario
            # o asegurarse de que Pydantic las maneje correctamente.
            # Pydantic v2 maneja objetos datetime directamente.
            # result['created_at'] = result['created_at'].isoformat() if result.get('created_at') else None
            # result['updated_at'] = result['updated_at'].isoformat() if result.get('updated_at') else None
            # result['closed_at'] = result['closed_at'].isoformat() if result.get('closed_at') else None
            print(f"CRUD: Ticket recuperado de BD: {result.get('id')}")
            return models.TicketResponse(**result)
        return None
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al obtener ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos al obtener ticket: {e}")
    except Exception as e:
        print(f"CRUD Error (General) al obtener ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado al obtener ticket: {e}")
    finally:
        if conn:
            conn.close()

async def get_all_tickets_from_db(filters: Optional[Dict[str, Any]] = None) -> List[models.TicketResponse]:
    """Obtiene todos los tickets, con filtros básicos."""
    base_sql = "SELECT * FROM tickets"
    conditions = []
    args = []

    if filters:
        for key, value in filters.items():
            if value is not None: # Solo añadir condición si el valor del filtro no es None
                # Asegurarse de que la clave es una columna válida para evitar inyección SQL
                # (aunque aquí los keys vienen de parámetros Query definidos)
                if key in ["status", "category", "user_id_telegram", "priority", "source"]: # Columnas permitidas para filtrar
                    conditions.append(f"{key} = %s")
                    args.append(value)
                elif key == "problem_description_contains": # Ejemplo de filtro LIKE
                    conditions.append("problem_description LIKE %s")
                    args.append(f"%{value}%")


    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)
    
    base_sql += " ORDER BY created_at DESC" # Ordenar por más reciente por defecto

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(base_sql, tuple(args))
            results = cursor.fetchall()
        
        print(f"CRUD: Recuperados {len(results)} tickets de la BD. Query: {base_sql} Args: {args}")
        return [models.TicketResponse(**row) for row in results]
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al listar tickets: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos al listar tickets: {e}")
    except Exception as e:
        print(f"CRUD Error (General) al listar tickets: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado al listar tickets: {e}")
    finally:
        if conn:
            conn.close()

# --- Funciones CRUD para FAQs ---

async def create_faq_in_db(faq_data: models.FAQCreate) -> models.FAQResponse:
    """Crea una nueva FAQ en la base de datos."""
    faq_id = f"FAQ-{str(uuid.uuid4())[:8].upper()}" # Generar ID si no se provee uno
    # created_at y updated_at son manejados por la BD.
    
    # Convertir lista de keywords a string si es necesario (ej. separada por comas)
    keywords_str = ",".join(faq_data.keywords) if faq_data.keywords else None

    sql = """
    INSERT INTO faqs (id, question, answer, category, keywords)
    VALUES (%s, %s, %s, %s, %s)
    """
    args = (
        faq_id,
        faq_data.question,
        faq_data.answer,
        faq_data.category,
        keywords_str
    )
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
        conn.commit()
        
        # Recuperar la FAQ creada para devolver el objeto completo
        created_faq = await get_faq_from_db_by_id(faq_id) # Necesitaremos esta función
        if not created_faq:
            raise Exception("FAQ creada pero no pudo ser recuperada.")
        print(f"CRUD: FAQ creada con ID {faq_id} en la BD.")
        return created_faq
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al crear FAQ: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos al crear FAQ: {e}")
    except Exception as e:
        print(f"CRUD Error (General) al crear FAQ: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado al crear FAQ: {e}")
    finally:
        if conn:
            conn.close()

async def get_faq_from_db_by_id(faq_id: str) -> Optional[models.FAQResponse]:
    """Obtiene una FAQ de la base de datos por su ID."""
    sql = "SELECT * FROM faqs WHERE id = %s"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, (faq_id,))
            result = cursor.fetchone()
        if result:
            # Convertir keywords de string a lista si es necesario
            if result.get('keywords') and isinstance(result['keywords'], str):
                result['keywords'] = [k.strip() for k in result['keywords'].split(',')]
            else:
                result['keywords'] = []
            return models.FAQResponse(**result)
        return None
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al obtener FAQ {faq_id}: {e}")
        # No relanzar HTTPException aquí si es para uso interno como en create_faq_in_db
        return None # O manejar el error de otra forma
    finally:
        if conn:
            conn.close()


async def get_faqs_from_db(query_term: Optional[str] = None, category_filter: Optional[str] = None) -> List[models.FAQResponse]:
    """Busca/obtiene FAQs de la base de datos."""
    base_sql = "SELECT * FROM faqs"
    conditions = []
    args = []

    if category_filter:
        conditions.append("category LIKE %s") # Usar LIKE para búsquedas parciales de categoría
        args.append(f"%{category_filter}%")
    
    if query_term:
        # Buscar en question, answer, y keywords
        query_like = f"%{query_term}%"
        conditions.append("(question LIKE %s OR answer LIKE %s OR keywords LIKE %s)")
        args.extend([query_like, query_like, query_like])

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)
    
    base_sql += " ORDER BY created_at DESC"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(base_sql, tuple(args))
            results = cursor.fetchall()

        faqs_list = []
        for row in results:
            if row.get('keywords') and isinstance(row['keywords'], str):
                row['keywords'] = [k.strip() for k in row['keywords'].split(',') if k.strip()]
            elif not row.get('keywords'):
                 row['keywords'] = []
            faqs_list.append(models.FAQResponse(**row))
        
        print(f"CRUD: Recuperadas {len(faqs_list)} FAQs de la BD. Query: {base_sql} Args: {args}")
        return faqs_list
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al listar FAQs: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos al listar FAQs: {e}")
    except Exception as e:
        print(f"CRUD Error (General) al listar FAQs: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado al listar FAQs: {e}")
    finally:
        if conn:
            conn.close()

# --- Funciones para actualizar y eliminar (necesarias para gestión completa) ---

async def update_ticket_status_in_db(ticket_id: str, status: str, resolution_details: Optional[str] = None, assigned_to: Optional[str] = None) -> Optional[models.TicketResponse]:
    """Actualiza el estado, detalles de resolución y/o asignado de un ticket."""
    fields_to_update = []
    args = []

    if status:
        fields_to_update.append("status = %s")
        args.append(status)
    if resolution_details is not None: # Permitir string vacío
        fields_to_update.append("resolution_details = %s")
        args.append(resolution_details)
    if assigned_to is not None:
        fields_to_update.append("assigned_to = %s")
        args.append(assigned_to)
    
    if not fields_to_update:
        # No hay nada que actualizar, podríamos devolver el ticket actual o un error.
        # Por ahora, devolvemos el ticket sin cambios.
        return await get_ticket_from_db(ticket_id)

    # `updated_at` se actualiza automáticamente por la BD.
    # Si el estado es "Cerrado" o "Resuelto", podríamos querer actualizar `closed_at`.
    if status and status.lower() in ["cerrado", "resuelto"]:
        fields_to_update.append("closed_at = CURRENT_TIMESTAMP") # O now()

    sql = f"UPDATE tickets SET {', '.join(fields_to_update)} WHERE id = %s"
    args.append(ticket_id)
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            rows_affected = cursor.execute(sql, tuple(args))
        conn.commit()
        
        if rows_affected > 0:
            print(f"CRUD: Ticket {ticket_id} actualizado en BD. Campos: {fields_to_update}")
            return await get_ticket_from_db(ticket_id) # Devolver el ticket actualizado
        else:
            print(f"CRUD: Ticket {ticket_id} no encontrado para actualizar o sin cambios.")
            return None # O el ticket original si no hubo error pero no se actualizó
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al actualizar ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos al actualizar ticket: {e}")
    finally:
        if conn:
            conn.close()


async def update_faq_in_db(faq_id: str, faq_update_data: models.FAQCreate) -> Optional[models.FAQResponse]:
    """Actualiza una FAQ existente."""
    keywords_str = ",".join(faq_update_data.keywords) if faq_update_data.keywords else None
    sql = """
    UPDATE faqs 
    SET question = %s, answer = %s, category = %s, keywords = %s 
    WHERE id = %s 
    """ # updated_at se actualiza automáticamente
    args = (
        faq_update_data.question,
        faq_update_data.answer,
        faq_update_data.category,
        keywords_str,
        faq_id
    )
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            rows_affected = cursor.execute(sql, args)
        conn.commit()
        if rows_affected > 0:
            print(f"CRUD: FAQ {faq_id} actualizada en BD.")
            return await get_faq_from_db_by_id(faq_id)
        else:
            print(f"CRUD: FAQ {faq_id} no encontrada para actualizar.")
            return None
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al actualizar FAQ {faq_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos al actualizar FAQ: {e}")
    finally:
        if conn:
            conn.close()

async def delete_faq_from_db(faq_id: str) -> bool:
    """Elimina una FAQ de la base de datos."""
    sql = "DELETE FROM faqs WHERE id = %s"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            rows_affected = cursor.execute(sql, (faq_id,))
        conn.commit()
        if rows_affected > 0:
            print(f"CRUD: FAQ {faq_id} eliminada de la BD.")
            return True
        print(f"CRUD: FAQ {faq_id} no encontrada para eliminar.")
        return False
    except pymysql.MySQLError as e:
        print(f"CRUD Error (MySQL) al eliminar FAQ {faq_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos al eliminar FAQ: {e}")
    finally:
        if conn:
            conn.close()

# Necesario para que el endpoint de la API pueda usarlo
from fastapi import HTTPException
