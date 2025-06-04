# backend/core/database.py

import pymysql
import os
from dotenv import load_dotenv
from pymysql.cursors import DictCursor # Para obtener resultados como diccionarios

# Cargar variables de entorno desde un archivo .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root") # Cambia según tu configuración
DB_PASSWORD = os.getenv("DB_PASSWORD", "") # Cambia según tu configuración
DB_NAME = os.getenv("DB_NAME", "cul_chatbot_db") # El nombre de tu BD
DB_PORT = int(os.getenv("DB_PORT", 3306)) # Puerto estándar de MySQL

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos MySQL."""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=DictCursor, # Devuelve filas como diccionarios
            charset='utf8mb4'       # Recomendado para soporte completo de Unicode
        )
        print(f"Conexión a la base de datos '{DB_NAME}' establecida exitosamente.")
        return connection
    except pymysql.MySQLError as e:
        print(f"Error al conectar a la base de datos MySQL: {e}")
        # En una aplicación real, podrías querer reintentar o manejar esto de forma más robusta.
        raise  # Re-lanza la excepción para que el llamador la maneje

# Ejemplo de cómo usarlo (no se ejecuta directamente aquí)
# if __name__ == "__main__":
#     try:
#         conn = get_db_connection()
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT VERSION();")
#             version = cursor.fetchone()
#             print(f"Versión de la Base de Datos: {version}")
#         conn.close()
#     except Exception as e:
#         print(f"No se pudo conectar o ejecutar la consulta: {e}")
