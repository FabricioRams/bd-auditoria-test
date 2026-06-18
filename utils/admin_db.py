import psycopg2
import streamlit as st

# Configuración de Neon.tech
NEON_HOST = 'ep-wild-glade-aih26ibl-pooler.c-4.us-east-1.aws.neon.tech'
NEON_DB = 'neondb'
NEON_USER = 'neondb_owner'
NEON_PASS = 'npg_dV8U1BNZfbus'

def get_admin_connection():
    """Retorna una conexión a la base de datos administrativa en Neon.tech"""
    return psycopg2.connect(
        host=NEON_HOST,
        database=NEON_DB,
        user=NEON_USER,
        password=NEON_PASS,
        sslmode='require'
    )
