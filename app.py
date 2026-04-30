import pandas as pd
import psycopg2
from psycopg2 import sql
import streamlit as st
import datetime

# --- CONFIGURACIÓN DE BASE DE DATOS ---
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

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Auditoría de Base de Datos", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; color: #0f172a;'>
        Panel de Auditoría PostgreSQL
    </h1>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 0. SISTEMA DE SEGURIDAD (LOGIN)
# ==========================================
# Inicializar el estado de la sesión si no existe
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def verificar_credenciales(usuario, contraseña):
    # Diccionario de credenciales permitidas
    usuarios_permitidos = {
        "fabricio": "admin123",
        "rodrigo": "dev456",
        "auditor_externo": "upt2026"
    }
    # Verificación
    if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == contraseña:
        return True
    return False

# Si no está autenticado, mostrar pantalla de login y detener el resto de la app
if not st.session_state['autenticado']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔒 Acceso Restringido</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sistema de Auditoría de Base de Datos</p>", unsafe_allow_html=True)
        
        # Formulario de Login
        with st.form("login_form"):
            usuario_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit_btn = st.form_submit_button("Ingresar al Dashboard", use_container_width=True)
            
            if submit_btn:
                if verificar_credenciales(usuario_input, password_input):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario_actual'] = usuario_input
                    st.rerun() # Recarga la página para mostrar el dashboard
                else:
                    st.error(" Credenciales incorrectas. Acceso denegado.")
    
    # st.stop() es la magia: evita que el código de abajo (el dashboard) se ejecute
    st.stop() 


# ==========================================
# A PARTIR DE AQUÍ VA TODO EL CÓDIGO DE TU DASHBOARD (El que pegaste antes)
# ==========================================

# --- CARGA DE DATOS ---
try:
    df = load_logs()
    # Creamos una columna auxiliar solo con la fecha (sin hora) para facilitar filtros y gráficos
    df['solo_fecha'] = df['fecha_hora'].dt.date
except Exception as exc:
    st.error(f"No se pudo consultar la tabla AUDITORIA_LOGS: {exc}")
    st.stop()

if df.empty:
    st.info("La tabla de auditoría está vacía. Realiza algunas operaciones en la base de datos.")
    st.stop()

# ==========================================
# 1. BARRA LATERAL (FILTROS AVANZADOS)
# ==========================================
st.sidebar.header("Filtros Avanzados")

# --- PANEL DE USUARIO (En la barra lateral) ---
st.sidebar.info(f" Auditor logueado: **{st.session_state['usuario_actual']}**")

if st.sidebar.button(" Cerrar Sesión", use_container_width=True):
    st.session_state['autenticado'] = False
    st.rerun()

st.sidebar.markdown("---")

# Filtro: Rango de Fechas
fecha_min = df['solo_fecha'].min()
fecha_max = df['solo_fecha'].max()
# Si hay un solo día, evitamos errores en el date_input
if fecha_min == fecha_max:
    fecha_rango = st.sidebar.date_input("Rango de Fechas", fecha_min)
    rango_inicio, rango_fin = fecha_rango, fecha_rango
else:
    fecha_rango = st.sidebar.date_input("Rango de Fechas", [fecha_min, fecha_max])
    if len(fecha_rango) == 2:
        rango_inicio, rango_fin = fecha_rango
    else:
        rango_inicio, rango_fin = fecha_rango[0], fecha_rango[0]

# Filtro: Usuario
usuarios_disponibles = sorted(df["usuario_bd"].dropna().unique().tolist())
usuarios_seleccionados = st.sidebar.multiselect("Usuario de BD", options=usuarios_disponibles, default=usuarios_disponibles)

# Filtro: Tabla
tablas_disponibles = sorted(df["tabla_nombre"].dropna().unique().tolist())
tablas_seleccionadas = st.sidebar.multiselect("Tabla", options=tablas_disponibles, default=tablas_disponibles)

# Filtro: Operación
operaciones_disponibles = ["I", "U", "D"]
operaciones_seleccionadas = st.sidebar.multiselect("Operación", options=operaciones_disponibles, default=operaciones_disponibles)

# --- APLICAR FILTROS ---
df_filtrado = df[
    (df["operacion"].isin(operaciones_seleccionadas)) &
    (df["tabla_nombre"].isin(tablas_seleccionadas)) &
    (df["usuario_bd"].isin(usuarios_seleccionados)) &
    (df["solo_fecha"] >= rango_inicio) &
    (df["solo_fecha"] <= rango_fin)
]

# ==========================================
# 2. PANEL PRINCIPAL (KPIs Y GRÁFICOS)
# ==========================================

# --- TARJETAS DE MÉTRICAS (KPIs) ---
st.markdown("###  Resumen de Actividad")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Operaciones", value=len(df_filtrado))
with col2:
    st.metric(label="Nuevos (INSERT)", value=len(df_filtrado[df_filtrado['operacion'] == 'I']))
with col3:
    st.metric(label="Modificados (UPDATE)", value=len(df_filtrado[df_filtrado['operacion'] == 'U']))
with col4:
    st.metric(label="Eliminados (DELETE)", value=len(df_filtrado[df_filtrado['operacion'] == 'D']))

st.markdown("---")

# --- GRÁFICOS ---
st.markdown("###  Análisis Visual")
grafico_col1, grafico_col2 = st.columns(2)

with grafico_col1:
    st.write("**Operaciones por Tabla**")
    if not df_filtrado.empty:
        ops_por_tabla = df_filtrado['tabla_nombre'].value_counts()
        st.bar_chart(ops_por_tabla, color="#3b82f6")
    else:
        st.info("No hay datos para graficar.")

with grafico_col2:
    st.write("**Línea de Tiempo de Cambios**")
    if not df_filtrado.empty:
        ops_por_dia = df_filtrado['solo_fecha'].value_counts().sort_index()
        st.line_chart(ops_por_dia, color="#ef4444")
    else:
        st.info("No hay datos para graficar.")

st.markdown("---")

# ==========================================
# 3. TABLA DE REGISTROS Y DESCARGA
# ==========================================
st.markdown("###  Registro Detallado de Auditoría")

# Mostramos la tabla sin la columna auxiliar 'solo_fecha'
st.dataframe(df_filtrado.drop(columns=['solo_fecha']), use_container_width=True)

# Botón para descargar
@st.cache_data
def convert_df(df_to_convert):
    return df_to_convert.to_csv(index=False).encode('utf-8')

csv = convert_df(df_filtrado.drop(columns=['solo_fecha']))
st.download_button(
    label=" Descargar Reporte en CSV",
    data=csv,
    file_name='reporte_auditoria.csv',
    mime='text/csv',
)