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
        creds = st.session_state["db_creds"]
        if isinstance(creds, dict):
            return psycopg2.connect(**creds)
        else:
            return psycopg2.connect(creds)

    # Plan B: Si la app detecta una URL en secretos (nube), se conecta a Neon.
    if "DATABASE_URL" in st.secrets:
        return psycopg2.connect(st.secrets["DATABASE_URL"])

    # Plan C: Usa la configuración local por defecto.
    return psycopg2.connect(**DB_CONFIG)


@st.cache_data(ttl=2)
def load_logs():
    conn = get_connection()
    query = sql.SQL(
        """
        SELECT *
        FROM public.AUDITORIA_LOGS
        ORDER BY fecha_hora DESC
        """
    )
    return pd.read_sql_query(query.as_string(conn), conn)
