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

#@st.cache_resource
def get_connection():
    # Si la app detecta una URL en los "Secretos" (en la nube), se conecta a Neon
    if "DATABASE_URL" in st.secrets:
        return psycopg2.connect(st.secrets["DATABASE_URL"])
    # Si no, usa la conexión de tu Docker local
    else:
        return psycopg2.connect(host="localhost", port=5432, dbname="postgres", user="postgres", password="superpassword")

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
# CARGAR DATOS (ANTES DE LAS PESTAÑAS)
# ==========================================
# Variable para almacenar el CSV cargado
if 'df_externo' not in st.session_state:
    st.session_state['df_externo'] = None

# --- CARGA DE DATOS DE LA BASE DE DATOS EN VIVO ---
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
# BARRA LATERAL GLOBAL (FILTROS AVANZADOS)
# ==========================================
st.sidebar.header("Filtros Avanzados")

# --- PANEL DE USUARIO (En la barra lateral) ---
st.sidebar.info(f" Auditor logueado: **{st.session_state['usuario_actual']}**")

if st.sidebar.button(" Cerrar Sesión", use_container_width=True):
    st.session_state['autenticado'] = False
    st.rerun()

st.sidebar.markdown("---")

# Mostrar filtros según si hay datos externos cargados
if st.session_state['df_externo'] is None:
    st.sidebar.subheader("📡 Filtros - Monitoreo en Vivo")
    
    # Filtro: Rango de Fechas
    fecha_min = df['solo_fecha'].min()
    fecha_max = df['solo_fecha'].max()
    if fecha_min == fecha_max:
        fecha_rango = st.sidebar.date_input("Rango de Fechas", fecha_min, key="fecha_vivo")
        rango_inicio, rango_fin = fecha_rango, fecha_rango
    else:
        fecha_rango = st.sidebar.date_input("Rango de Fechas", [fecha_min, fecha_max], key="fecha_vivo")
        if len(fecha_rango) == 2:
            rango_inicio, rango_fin = fecha_rango
        else:
            rango_inicio, rango_fin = fecha_rango[0], fecha_rango[0]

    # Filtro: Usuario
    usuarios_disponibles = sorted(df["usuario_bd"].dropna().unique().tolist())
    usuarios_seleccionados = st.sidebar.multiselect("Usuario de BD", options=usuarios_disponibles, default=usuarios_disponibles, key="usuario_vivo")

    # Filtro: Tabla
    tablas_disponibles = sorted(df["tabla_nombre"].dropna().unique().tolist())
    tablas_seleccionadas = st.sidebar.multiselect("Tabla", options=tablas_disponibles, default=tablas_disponibles, key="tabla_vivo")

    # Filtro: Operación
    operaciones_disponibles = ["I", "U", "D"]
    operaciones_seleccionadas = st.sidebar.multiselect("Operación", options=operaciones_disponibles, default=operaciones_disponibles, key="operacion_vivo")
    
    # Guardar en session state para usarlos en la pestaña
    st.session_state['rango_inicio_vivo'] = rango_inicio
    st.session_state['rango_fin_vivo'] = rango_fin
    st.session_state['usuarios_seleccionados_vivo'] = usuarios_seleccionados
    st.session_state['tablas_seleccionadas_vivo'] = tablas_seleccionadas
    st.session_state['operaciones_seleccionadas_vivo'] = operaciones_seleccionadas
else:
    st.sidebar.subheader("📁 Filtros - Archivo CSV")
    
    df_ext = st.session_state['df_externo']
    
    # Filtro: Rango de Fechas (si existe)
    if 'solo_fecha' in df_ext.columns:
        fecha_min = df_ext['solo_fecha'].min()
        fecha_max = df_ext['solo_fecha'].max()
        if fecha_min == fecha_max:
            fecha_rango = st.sidebar.date_input("Rango de Fechas", fecha_min, key="fecha_csv")
            rango_inicio, rango_fin = fecha_rango, fecha_rango
        else:
            fecha_rango = st.sidebar.date_input("Rango de Fechas", [fecha_min, fecha_max], key="fecha_csv")
            if len(fecha_rango) == 2:
                rango_inicio, rango_fin = fecha_rango
            else:
                rango_inicio, rango_fin = fecha_rango[0], fecha_rango[0]
        st.session_state['rango_inicio_csv'] = rango_inicio
        st.session_state['rango_fin_csv'] = rango_fin
    
    # Filtro: Usuario (si existe)
    if 'usuario_bd' in df_ext.columns:
        usuarios_disponibles = sorted(df_ext["usuario_bd"].dropna().unique().tolist())
        usuarios_seleccionados = st.sidebar.multiselect("Usuario de BD", options=usuarios_disponibles, default=usuarios_disponibles, key="usuario_csv")
        st.session_state['usuarios_seleccionados_csv'] = usuarios_seleccionados
    
    # Filtro: Tabla (si existe)
    if 'tabla_nombre' in df_ext.columns:
        tablas_disponibles = sorted(df_ext["tabla_nombre"].dropna().unique().tolist())
        tablas_seleccionadas = st.sidebar.multiselect("Tabla", options=tablas_disponibles, default=tablas_disponibles, key="tabla_csv")
        st.session_state['tablas_seleccionadas_csv'] = tablas_seleccionadas
    
    # Filtro: Operación (si existe)
    if 'operacion' in df_ext.columns:
        operaciones_disponibles = sorted(df_ext["operacion"].dropna().unique().tolist())
        operaciones_seleccionadas = st.sidebar.multiselect("Operación", options=operaciones_disponibles, default=operaciones_disponibles, key="operacion_csv")
        st.session_state['operaciones_seleccionadas_csv'] = operaciones_seleccionadas

# ==========================================
# SISTEMA DE PESTAÑAS (TABS)
# ==========================================
tab_vivo, tab_csv = st.tabs(["📡 Monitoreo en Vivo (Neon)", "📁 Cargar Archivo CSV"])

# PESTAÑA 1: CONEXIÓN A LA BASE DE DATOS EN VIVO
# ==========================================
with tab_vivo:

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

    # Recuperar filtros del session state (creados en el sidebar global)
    rango_inicio = st.session_state.get('rango_inicio_vivo', df['solo_fecha'].min())
    rango_fin = st.session_state.get('rango_fin_vivo', df['solo_fecha'].max())
    usuarios_seleccionados = st.session_state.get('usuarios_seleccionados_vivo', sorted(df["usuario_bd"].dropna().unique().tolist()))
    tablas_seleccionadas = st.session_state.get('tablas_seleccionadas_vivo', sorted(df["tabla_nombre"].dropna().unique().tolist()))
    operaciones_seleccionadas = st.session_state.get('operaciones_seleccionadas_vivo', ["I", "U", "D"])

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


# PESTAÑA 2: CARGADOR DE ARCHIVOS CSV
# ==========================================
with tab_csv:
    st.markdown("### Análisis de Logs Externos")
    st.info("Sube un reporte histórico de PostgreSQL o MySQL en formato .csv para analizarlo sin conexión a la base de datos.")
    
    # El widget mágico de Streamlit para subir archivos
    archivo_subido = st.file_uploader("Selecciona un archivo CSV", type=["csv"])
    
    if archivo_subido is not None:
        try:
            # Pandas lee el archivo que subió el usuario
            df_externo = pd.read_csv(archivo_subido)
            
            # Convertir columna de fecha a datetime si existe
            if 'fecha_hora' in df_externo.columns:
                df_externo['fecha_hora'] = pd.to_datetime(df_externo['fecha_hora'])
                df_externo['solo_fecha'] = df_externo['fecha_hora'].dt.date
            
            # Guardar en session_state para que el sidebar lo detecte
            st.session_state['df_externo'] = df_externo
            
            st.success("✅ ¡Archivo procesado correctamente!")
            
            # Mostramos un resumen
            col_a, col_b = st.columns(2)
            col_a.metric("Total de Filas", len(df_externo))
            col_b.metric("Columnas Detectadas", len(df_externo.columns))
            
            st.markdown("---")
            
            # Recuperar filtros del sidebar (session state)
            if 'rango_inicio_csv' in st.session_state:
                rango_inicio = st.session_state.get('rango_inicio_csv', df_externo['solo_fecha'].min())
                rango_fin = st.session_state.get('rango_fin_csv', df_externo['solo_fecha'].max())
                usuarios_seleccionados = st.session_state.get('usuarios_seleccionados_csv', [])
                tablas_seleccionadas = st.session_state.get('tablas_seleccionadas_csv', [])
                operaciones_seleccionadas = st.session_state.get('operaciones_seleccionadas_csv', [])
                
                # --- APLICAR FILTROS ---
                df_filtrado_csv = df_externo.copy()
                
                if 'operacion' in df_filtrado_csv.columns and operaciones_seleccionadas:
                    df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["operacion"].isin(operaciones_seleccionadas)]
                
                if 'tabla_nombre' in df_filtrado_csv.columns and tablas_seleccionadas:
                    df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["tabla_nombre"].isin(tablas_seleccionadas)]
                
                if 'usuario_bd' in df_filtrado_csv.columns and usuarios_seleccionados:
                    df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["usuario_bd"].isin(usuarios_seleccionados)]
                
                if 'solo_fecha' in df_filtrado_csv.columns:
                    df_filtrado_csv = df_filtrado_csv[
                        (df_filtrado_csv["solo_fecha"] >= rango_inicio) &
                        (df_filtrado_csv["solo_fecha"] <= rango_fin)
                    ]
            else:
                df_filtrado_csv = df_externo.copy()
            
            st.markdown("---")
            
            # Mostrar estadísticas de lo filtrado
            st.markdown("### 📊 Resumen Filtrado")
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            
            with stat_col1:
                st.metric("Registros Mostrados", len(df_filtrado_csv))
            
            if 'operacion' in df_filtrado_csv.columns:
                with stat_col2:
                    insert_count = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'I']) if 'I' in df_filtrado_csv['operacion'].values else 0
                    update_count = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'U']) if 'U' in df_filtrado_csv['operacion'].values else 0
                    delete_count = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'D']) if 'D' in df_filtrado_csv['operacion'].values else 0
                    st.metric("Total de Cambios", f"I:{insert_count} U:{update_count} D:{delete_count}")
            
            if 'tabla_nombre' in df_filtrado_csv.columns:
                with stat_col3:
                    tablas_count = df_filtrado_csv['tabla_nombre'].nunique()
                    st.metric("Tablas Afectadas", tablas_count)
            
            st.markdown("---")
            
            # Mostramos la tabla interactiva
            st.markdown("### 📋 Datos del CSV")
            columnas_mostrar = [col for col in df_filtrado_csv.columns if col != 'solo_fecha']
            st.dataframe(df_filtrado_csv[columnas_mostrar], use_container_width=True)
            
            # Botón para descargar los datos filtrados
            @st.cache_data
            def convert_df_csv(df_to_convert):
                return df_to_convert.to_csv(index=False).encode('utf-8')
            
            csv_filtrado = convert_df_csv(df_filtrado_csv[columnas_mostrar])
            st.download_button(
                label="⬇️ Descargar Datos Filtrados (CSV)",
                data=csv_filtrado,
                file_name='reporte_filtrado.csv',
                mime='text/csv',
            )
            
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.session_state['df_externo'] = None
