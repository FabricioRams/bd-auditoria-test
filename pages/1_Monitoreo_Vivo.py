import streamlit as st

from database import load_logs
from streamlit_autorefresh import st_autorefresh

if not st.session_state.get("autenticado", False):
    st.warning("Debes iniciar sesion para ver esta pagina.")
    st.stop()

st.title("Monitoreo en Vivo")

# --- CARGA DE DATOS ---
try:
    df = load_logs()
    df["solo_fecha"] = df["fecha_hora"].dt.date
except Exception as exc:
    st.error(f"No se pudo consultar la tabla AUDITORIA_LOGS: {exc}")
    st.stop()

if df.empty:
    st.info("La tabla de auditoria esta vacia. Realiza algunas operaciones en la base de datos.")
    st.stop()

# ==========================================
# BARRA LATERAL (FILTROS AVANZADOS)
# ==========================================
st.sidebar.markdown("### Modo Monitoreo")
auto_refresh = st.sidebar.checkbox("Activar recarga ")

if auto_refresh:
    # Recarga la página sola cada 5000 milisegundos (5 segundos)
    st_autorefresh(interval=5000, key="datarefresh")

st.sidebar.markdown("---")

st.sidebar.header("Filtros Avanzados")
st.sidebar.info(f"Auditor logueado: {st.session_state.get('usuario_actual', 'N/A')}")

if st.sidebar.button("Cerrar Sesion", use_container_width=True, key="logout_vivo"):
    st.session_state["autenticado"] = False
    st.rerun()

st.sidebar.markdown("---")

fecha_min = df["solo_fecha"].min()
fecha_max = df["solo_fecha"].max()

if fecha_min == fecha_max:
    fecha_rango = st.sidebar.date_input("Rango de Fechas", fecha_min, key="fecha_vivo")
    rango_inicio, rango_fin = fecha_rango, fecha_rango
else:
    fecha_rango = st.sidebar.date_input("Rango de Fechas", [fecha_min, fecha_max], key="fecha_vivo")
    if len(fecha_rango) == 2:
        rango_inicio, rango_fin = fecha_rango
    else:
        rango_inicio, rango_fin = fecha_rango[0], fecha_rango[0]

usuarios_disponibles = sorted(df["usuario_bd"].dropna().unique().tolist())
usuarios_seleccionados = st.sidebar.multiselect(
    "Usuario de BD",
    options=usuarios_disponibles,
    default=usuarios_disponibles,
    key="usuario_vivo",
)

tablas_disponibles = sorted(df["tabla_nombre"].dropna().unique().tolist())
tablas_seleccionadas = st.sidebar.multiselect(
    "Tabla",
    options=tablas_disponibles,
    default=tablas_disponibles,
    key="tabla_vivo",
)

operaciones_disponibles = ["I", "U", "D"]
operaciones_seleccionadas = st.sidebar.multiselect(
    "Operacion",
    options=operaciones_disponibles,
    default=operaciones_disponibles,
    key="operacion_vivo",
)

# Persistir variables globales en session_state.
st.session_state["rango_inicio_vivo"] = rango_inicio
st.session_state["rango_fin_vivo"] = rango_fin
st.session_state["usuarios_seleccionados_vivo"] = usuarios_seleccionados
st.session_state["tablas_seleccionadas_vivo"] = tablas_seleccionadas
st.session_state["operaciones_seleccionadas_vivo"] = operaciones_seleccionadas

# --- APLICAR FILTROS ---
df_filtrado = df[
    (df["operacion"].isin(operaciones_seleccionadas))
    & (df["tabla_nombre"].isin(tablas_seleccionadas))
    & (df["usuario_bd"].isin(usuarios_seleccionados))
    & (df["solo_fecha"] >= rango_inicio)
    & (df["solo_fecha"] <= rango_fin)
]

# ==========================================
# PANEL PRINCIPAL (KPIs Y GRAFICOS)
# ==========================================
st.markdown("### Resumen de Actividad")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Operaciones", value=len(df_filtrado))
with col2:
    st.metric(label="Nuevos (INSERT)", value=len(df_filtrado[df_filtrado["operacion"] == "I"]))
with col3:
    st.metric(label="Modificados (UPDATE)", value=len(df_filtrado[df_filtrado["operacion"] == "U"]))
with col4:
    st.metric(label="Eliminados (DELETE)", value=len(df_filtrado[df_filtrado["operacion"] == "D"]))

st.markdown("---")
st.markdown("### Analisis Visual")
grafico_col1, grafico_col2 = st.columns(2)

with grafico_col1:
    st.write("Operaciones por Tabla")
    if not df_filtrado.empty:
        ops_por_tabla = df_filtrado["tabla_nombre"].value_counts()
        st.bar_chart(ops_por_tabla, color="#3b82f6")
    else:
        st.info("No hay datos para graficar.")

with grafico_col2:
    st.write("Linea de Tiempo de Cambios")
    if not df_filtrado.empty:
        ops_por_dia = df_filtrado["solo_fecha"].value_counts().sort_index()
        st.line_chart(ops_por_dia, color="#ef4444")
    else:
        st.info("No hay datos para graficar.")

st.markdown("---")
st.markdown("### Registro Detallado de Auditoria")
st.dataframe(df_filtrado.drop(columns=["solo_fecha"]), use_container_width=True)


@st.cache_data
def convert_df(df_to_convert):
    return df_to_convert.to_csv(index=False).encode("utf-8")


csv = convert_df(df_filtrado.drop(columns=["solo_fecha"]))
st.download_button(
    label="Descargar Reporte en CSV",
    data=csv,
    file_name="reporte_auditoria.csv",
    mime="text/csv",
)
