import pandas as pd
import streamlit as st


if not st.session_state.get("autenticado", False):
    st.warning("Debes iniciar sesion para ver esta pagina.")
    st.stop()

if "df_externo" not in st.session_state:
    st.session_state["df_externo"] = None

st.title("Cargar Archivo CSV")
st.markdown("### Analisis de Logs Externos")
st.info("Sube un reporte historico de PostgreSQL o MySQL en formato .csv para analizarlo sin conexion a la base de datos.")

archivo_subido = st.file_uploader("Selecciona un archivo CSV", type=["csv"], key="uploader_csv")

if archivo_subido is not None:
    try:
        df_externo = pd.read_csv(archivo_subido)

        if "fecha_hora" in df_externo.columns:
            df_externo["fecha_hora"] = pd.to_datetime(df_externo["fecha_hora"])
            df_externo["solo_fecha"] = df_externo["fecha_hora"].dt.date

        st.session_state["df_externo"] = df_externo
        st.success("Archivo procesado correctamente.")
    except Exception as exc:
        st.error(f"Error al leer el archivo: {exc}")
        st.session_state["df_externo"] = None

if st.session_state["df_externo"] is None:
    st.info("Carga un archivo CSV para comenzar el analisis.")
    st.stop()

df_externo = st.session_state["df_externo"]

# ==========================================
# BARRA LATERAL (FILTROS CSV)
# ==========================================
st.sidebar.header("Filtros CSV")
st.sidebar.info(f"Auditor logueado: {st.session_state.get('usuario_actual', 'N/A')}")

if st.sidebar.button("Cerrar Sesion", use_container_width=True, key="logout_csv"):
    st.session_state["autenticado"] = False
    st.rerun()

st.sidebar.markdown("---")

rango_inicio = None
rango_fin = None

if "solo_fecha" in df_externo.columns:
    fecha_min = df_externo["solo_fecha"].min()
    fecha_max = df_externo["solo_fecha"].max()
    if fecha_min == fecha_max:
        fecha_rango = st.sidebar.date_input("Rango de Fechas", fecha_min, key="fecha_csv")
        rango_inicio, rango_fin = fecha_rango, fecha_rango
    else:
        fecha_rango = st.sidebar.date_input("Rango de Fechas", [fecha_min, fecha_max], key="fecha_csv")
        if len(fecha_rango) == 2:
            rango_inicio, rango_fin = fecha_rango
        else:
            rango_inicio, rango_fin = fecha_rango[0], fecha_rango[0]

usuarios_seleccionados = None
if "usuario_bd" in df_externo.columns:
    usuarios_disponibles = sorted(df_externo["usuario_bd"].dropna().unique().tolist())
    usuarios_seleccionados = st.sidebar.multiselect(
        "Usuario de BD",
        options=usuarios_disponibles,
        default=usuarios_disponibles,
        key="usuario_csv",
    )

tablas_seleccionadas = None
if "tabla_nombre" in df_externo.columns:
    tablas_disponibles = sorted(df_externo["tabla_nombre"].dropna().unique().tolist())
    tablas_seleccionadas = st.sidebar.multiselect(
        "Tabla",
        options=tablas_disponibles,
        default=tablas_disponibles,
        key="tabla_csv",
    )

operaciones_seleccionadas = None
if "operacion" in df_externo.columns:
    operaciones_disponibles = sorted(df_externo["operacion"].dropna().unique().tolist())
    operaciones_seleccionadas = st.sidebar.multiselect(
        "Operacion",
        options=operaciones_disponibles,
        default=operaciones_disponibles,
        key="operacion_csv",
    )

# Persistir variables globales en session_state.
if rango_inicio is not None and rango_fin is not None:
    st.session_state["rango_inicio_csv"] = rango_inicio
    st.session_state["rango_fin_csv"] = rango_fin
if usuarios_seleccionados is not None:
    st.session_state["usuarios_seleccionados_csv"] = usuarios_seleccionados
if tablas_seleccionadas is not None:
    st.session_state["tablas_seleccionadas_csv"] = tablas_seleccionadas
if operaciones_seleccionadas is not None:
    st.session_state["operaciones_seleccionadas_csv"] = operaciones_seleccionadas

# --- APLICAR FILTROS ---
df_filtrado_csv = df_externo.copy()

if "operacion" in df_filtrado_csv.columns and operaciones_seleccionadas is not None:
    df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["operacion"].isin(operaciones_seleccionadas)]
if "tabla_nombre" in df_filtrado_csv.columns and tablas_seleccionadas is not None:
    df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["tabla_nombre"].isin(tablas_seleccionadas)]
if "usuario_bd" in df_filtrado_csv.columns and usuarios_seleccionados is not None:
    df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["usuario_bd"].isin(usuarios_seleccionados)]
if "solo_fecha" in df_filtrado_csv.columns and rango_inicio is not None and rango_fin is not None:
    df_filtrado_csv = df_filtrado_csv[
        (df_filtrado_csv["solo_fecha"] >= rango_inicio)
        & (df_filtrado_csv["solo_fecha"] <= rango_fin)
    ]

# ==========================================
# VISTA PRINCIPAL CSV
# ==========================================
col_a, col_b = st.columns(2)
col_a.metric("Total de Filas", len(df_externo))
col_b.metric("Columnas Detectadas", len(df_externo.columns))

st.markdown("---")
st.markdown("### Resumen Filtrado")
stat_col1, stat_col2, stat_col3 = st.columns(3)

with stat_col1:
    st.metric("Registros Mostrados", len(df_filtrado_csv))

if "operacion" in df_filtrado_csv.columns:
    with stat_col2:
        insert_count = len(df_filtrado_csv[df_filtrado_csv["operacion"] == "I"])
        update_count = len(df_filtrado_csv[df_filtrado_csv["operacion"] == "U"])
        delete_count = len(df_filtrado_csv[df_filtrado_csv["operacion"] == "D"])
        st.metric("Total de Cambios", f"I:{insert_count} U:{update_count} D:{delete_count}")

if "tabla_nombre" in df_filtrado_csv.columns:
    with stat_col3:
        tablas_count = df_filtrado_csv["tabla_nombre"].nunique()
        st.metric("Tablas Afectadas", tablas_count)

st.markdown("---")
st.markdown("### Datos del CSV")
columnas_mostrar = [col for col in df_filtrado_csv.columns if col != "solo_fecha"]
st.dataframe(df_filtrado_csv[columnas_mostrar], use_container_width=True)


@st.cache_data
def convert_df_csv(df_to_convert):
    return df_to_convert.to_csv(index=False).encode("utf-8")


csv_filtrado = convert_df_csv(df_filtrado_csv[columnas_mostrar])
st.download_button(
    label="Descargar Datos Filtrados (CSV)",
    data=csv_filtrado,
    file_name="reporte_filtrado.csv",
    mime="text/csv",
)
