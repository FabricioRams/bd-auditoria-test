import pandas as pd
import psycopg2
from psycopg2 import sql
import streamlit as st

# --- CONFIGURACION DE BASE DE DATOS ---
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "superpassword",
}

def get_connection():
    # Plan A: Usa credenciales de la sesión si existen
    if "db_creds" in st.session_state and st.session_state["db_creds"]:
        creds = st.session_state["db_creds"].copy()
        motor = creds.pop("motor", "PostgreSQL")
        
        if motor == "PostgreSQL":
            import psycopg2
            return psycopg2.connect(**creds)
        elif motor == "MySQL":
            import pymysql
            return pymysql.connect(**creds)
        elif motor == "SQLite":
            import sqlite3
            return sqlite3.connect(creds["path"])
        elif motor == "MongoDB":
            from pymongo import MongoClient
            return MongoClient(creds["uri"])

    # Plan B: Si la app detecta una URL en secretos (nube), se conecta a Neon/Postgres.
    if "DATABASE_URL" in st.secrets:
        import psycopg2
        return psycopg2.connect(st.secrets["DATABASE_URL"])

    # Plan C: Usa la configuración local por defecto (PostgreSQL).
    import psycopg2
    return psycopg2.connect(**DB_CONFIG)

@st.cache_data(ttl=2)
def load_logs():
    conn = get_connection()
    
    motor = "PostgreSQL"
    if "db_creds" in st.session_state and st.session_state["db_creds"]:
        motor = st.session_state["db_creds"].get("motor", "PostgreSQL")
        
    if motor == "MongoDB":
        db_name = st.session_state["db_creds"]["dbname"]
        db = conn[db_name]
        
        if "AUDITORIA_LOGS" in db.list_collection_names():
            logs = list(db["AUDITORIA_LOGS"].find().sort("fecha_hora", -1))
            if logs:
                df = pd.DataFrame(logs)
                # Asegurar de que la columna _id de MongoDB no rompa nada si no se necesita
                if "_id" in df.columns:
                    df = df.drop(columns=["_id"])
                return df
                
        # Retornar DataFrame vacío con las columnas esperadas
        return pd.DataFrame(columns=["log_id", "tabla_nombre", "operacion", "usuario_bd", "ip_cliente", "fecha_hora", "valores_old", "valores_new"])

    # Lógica para motores SQL
    try:
        query = sql.SQL(
            """
            SELECT *
            FROM public.AUDITORIA_LOGS
            ORDER BY fecha_hora DESC
            """
        )
        return pd.read_sql_query(query.as_string(conn), conn)
    except Exception:
        # Fallback genérico para SQLite / MySQL
        query = "SELECT * FROM AUDITORIA_LOGS ORDER BY fecha_hora DESC"
        return pd.read_sql_query(query, conn)
