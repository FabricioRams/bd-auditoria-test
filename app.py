import pandas as pd
import psycopg2
from psycopg2 import sql
import streamlit as st


DB_CONFIG = {
	"host": "localhost",
	"port": 5432,
	"dbname": "postgres",
	"user": "postgres",
	"password": "superpassword",
}


@st.cache_resource
def get_connection():
	return psycopg2.connect(**DB_CONFIG)


@st.cache_data(ttl=30)
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


st.set_page_config(page_title="Auditoria de Base de Datos", layout="wide")

st.markdown(
	"""
	<h1 style='text-align: center; color: #0f172a;'>
		Panel de Auditoria PostgreSQL
	</h1>
	<p style='text-align: center; color: #475569; margin-top: -10px;'>
		Explora los eventos de INSERT, UPDATE y DELETE en tiempo real.
	</p>
	""",
	unsafe_allow_html=True,
)

try:
	df = load_logs()
except Exception as exc:
	st.error(f"No se pudo consultar la tabla AUDITORIA_LOGS: {exc}")
	st.stop()

st.sidebar.header("Filtros")

operaciones_disponibles = ["I", "U", "D"]
operaciones_seleccionadas = st.sidebar.multiselect(
	"Operacion",
	options=operaciones_disponibles,
	default=operaciones_disponibles,
)

tablas_disponibles = sorted(df["tabla_nombre"].dropna().unique().tolist())
tablas_seleccionadas = st.sidebar.multiselect(
	"Tabla",
	options=tablas_disponibles,
	default=tablas_disponibles,
)

df_filtrado = df[
	df["operacion"].isin(operaciones_seleccionadas)
	& df["tabla_nombre"].isin(tablas_seleccionadas)
]

st.dataframe(df_filtrado, use_container_width=True)
