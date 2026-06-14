import streamlit as st
import pandas as pd
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.styles import GLOBAL_CSS, page_header, section_title
from utils.database import load_logs
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Monitoreo en Vivo — AuditDB", layout="wide", page_icon="📡")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if not st.session_state.get("autenticado", False):
    st.markdown("""<div style="text-align:center; padding:3rem; color:#475569;">
        <div style="font-size:2rem; margin-bottom:1rem;">🔒</div>
        <p>Acceso denegado. <a href="/" style="color:#3b82f6;">Inicia sesión</a></p>
    </div>""", unsafe_allow_html=True)
    st.stop()

page_header("O", "Monitoreo en Vivo", "Registro de cambios en tiempo real")

# ===== CARGAR DATOS =====
try:
    df = load_logs()
    if df.empty:
        st.markdown("""
        <div style="text-align:center; padding:3rem; border:1px dashed #1e2d4d; border-radius:12px; margin-top:1rem;">
            <div style="font-size:2.5rem; margin-bottom:1rem;">📭</div>
            <h3 style="color:#475569; margin:0;">Sin eventos registrados</h3>
            <p style="color:#334155; font-size:0.875rem; margin-top:0.5rem;">La tabla de auditoría está vacía. Realiza operaciones en la base de datos conectada.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    df["solo_fecha"] = df["fecha_hora"].dt.date
except Exception as exc:
    st.error(f"No se pudo consultar AUDITORIA_LOGS: {exc}")
    st.stop()

# ===== BARRA SUPERIOR =====
top_col1, top_col2, top_col3 = st.columns([3, 2, 1])
with top_col1:
    auto_refresh = st.checkbox("  Recarga automática (cada 5 s)")
    if auto_refresh:
        st_autorefresh(interval=5000, key="datarefresh")
with top_col2:
    user_now = st.session_state.get('usuario_actual', 'N/A')
    st.markdown(f"""
    <div style="background:#0f1628; border:1px solid #1e2d4d; border-radius:8px;
                padding:0.5rem 0.875rem; font-size:0.78rem; color:#94a3b8; margin-top:0.25rem;">
         Auditor: <strong style="color:#e2e8f0;">{user_now}</strong>
    </div>
    """, unsafe_allow_html=True)
with top_col3:
    if st.button("Cerrar sesión", use_container_width=True, key="logout_vivo"):
        st.session_state["autenticado"] = False
        st.rerun()

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ===== FILTROS =====
with st.expander("  Filtros avanzados", expanded=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    fecha_min = df["solo_fecha"].min()
    fecha_max = df["solo_fecha"].max()

    with col_f1:
        if fecha_min == fecha_max:
            fecha_rango = st.date_input("Rango de fechas", fecha_min, key="fecha_vivo")
            rango_inicio, rango_fin = fecha_rango, fecha_rango
        else:
            fecha_rango = st.date_input("Rango de fechas", [fecha_min, fecha_max], key="fecha_vivo")
            rango_inicio, rango_fin = (fecha_rango[0], fecha_rango[1]) if len(fecha_rango) == 2 else (fecha_rango[0], fecha_rango[0])

    with col_f2:
        usuarios_disponibles = sorted(df["usuario_bd"].dropna().unique().tolist())
        usuarios_seleccionados = st.multiselect("Usuario BD", options=usuarios_disponibles, default=usuarios_disponibles, key="usuario_vivo")

    with col_f3:
        tablas_disponibles = sorted(df["tabla_nombre"].dropna().unique().tolist())
        tablas_seleccionadas = st.multiselect("Tabla", options=tablas_disponibles, default=tablas_disponibles, key="tabla_vivo")

    with col_f4:
        OPS = {"I": "INSERT", "U": "UPDATE", "D": "DELETE"}
        operaciones_seleccionadas = st.multiselect(
            "Operación",
            options=["I", "U", "D"],
            default=["I", "U", "D"],
            format_func=lambda x: f"{OPS.get(x, x)}",
            key="operacion_vivo"
        )

# ===== APLICAR FILTROS =====
df_filtrado = df[
    df["operacion"].isin(operaciones_seleccionadas) &
    df["tabla_nombre"].isin(tablas_seleccionadas) &
    df["usuario_bd"].isin(usuarios_seleccionados) &
    (df["solo_fecha"] >= rango_inicio) &
    (df["solo_fecha"] <= rango_fin)
]

st.markdown("<hr>", unsafe_allow_html=True)

# ===== ALERTAS =====
section_title("Alertas de seguridad")
alertas = 0

if not df_filtrado.empty:
    num_deletes = len(df_filtrado[df_filtrado["operacion"] == "D"])
    if num_deletes > 10:
        st.markdown(f"""
        <div style="background:#ef444415; border:1px solid #ef444440; border-left:3px solid #ef4444;
                    border-radius:8px; padding:0.75rem 1rem; margin-bottom:0.5rem; font-size:0.875rem;">
             <strong style="color:#ef4444;">Eliminaciones masivas</strong> — Se detectaron <strong>{num_deletes}</strong> operaciones DELETE en el rango seleccionado.
        </div>
        """, unsafe_allow_html=True)
        alertas += 1

    horas = df_filtrado["fecha_hora"].dt.hour
    minutos = df_filtrado["fecha_hora"].dt.minute
    horario_inusual = df_filtrado[(horas < 6) | ((horas == 23) & (minutos == 59))]
    if not horario_inusual.empty:
        st.markdown(f"""
        <div style="background:#f59e0b15; border:1px solid #f59e0b40; border-left:3px solid #f59e0b;
                    border-radius:8px; padding:0.75rem 1rem; margin-bottom:0.5rem; font-size:0.875rem;">
             <strong style="color:#f59e0b;">Horario inusual</strong> — {len(horario_inusual)} operaciones entre las 11:59 PM y 06:00 AM.
        </div>
        """, unsafe_allow_html=True)
        alertas += 1

    for user, count in df_filtrado["usuario_bd"].value_counts().items():
        if count > 50:
            st.markdown(f"""
            <div style="background:#f59e0b15; border:1px solid #f59e0b40; border-left:3px solid #f59e0b;
                        border-radius:8px; padding:0.75rem 1rem; margin-bottom:0.5rem; font-size:0.875rem;">
                 <strong style="color:#f59e0b;">Actividad anormal</strong> — El usuario <code style="background:#050810; padding:1px 5px; border-radius:3px;">{user}</code> realizó <strong>{count}</strong> operaciones.
            </div>
            """, unsafe_allow_html=True)
            alertas += 1

if alertas == 0:
    st.markdown("""
    <div style="background:#10b98115; border:1px solid #10b98140; border-left:3px solid #10b981;
                border-radius:8px; padding:0.75rem 1rem; font-size:0.875rem;">
         <strong style="color:#10b981;">Sin anomalías detectadas</strong> — El sistema opera dentro de los parámetros normales.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ===== KPIs =====
section_title("Resumen de actividad")
k1, k2, k3, k4 = st.columns(4)

total = len(df_filtrado)
inserts = len(df_filtrado[df_filtrado["operacion"] == "I"])
updates = len(df_filtrado[df_filtrado["operacion"] == "U"])
deletes = len(df_filtrado[df_filtrado["operacion"] == "D"])

with k1:
    st.metric("Total de operaciones", f"{total:,}")
with k2:
    st.metric("INSERT", f"{inserts:,}", delta=None)
with k3:
    st.metric("UPDATE", f"{updates:,}", delta=None)
with k4:
    st.metric("DELETE", f"{deletes:,}", delta=None)

st.markdown("<hr>", unsafe_allow_html=True)

# ===== GRÁFICOS =====
section_title("Análisis visual")
g1, g2 = st.columns(2)

with g1:
    st.markdown("<p style='font-size:0.78rem; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:#475569; margin-bottom:0.5rem;'>Operaciones por tabla</p>", unsafe_allow_html=True)
    if not df_filtrado.empty:
        ops_por_tabla = df_filtrado["tabla_nombre"].value_counts()
        st.bar_chart(ops_por_tabla, color="#3b82f6")
    else:
        st.info("Sin datos para graficar.")

with g2:
    st.markdown("<p style='font-size:0.78rem; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:#475569; margin-bottom:0.5rem;'>Línea de tiempo de cambios</p>", unsafe_allow_html=True)
    if not df_filtrado.empty:
        ops_por_dia = df_filtrado["solo_fecha"].value_counts().sort_index()
        st.line_chart(ops_por_dia, color="#06b6d4")
    else:
        st.info("Sin datos para graficar.")

st.markdown("<hr>", unsafe_allow_html=True)

# ===== REGISTRO DETALLADO =====
section_title("Registro detallado de auditoría")
tab_tabla, tab_logs = st.tabs(["  Vista de tabla", "  Consola de logs"])

with tab_tabla:
    st.dataframe(df_filtrado.drop(columns=["solo_fecha"]), use_container_width=True, hide_index=True)

with tab_logs:
    log_lines = []
    OP_COLORS = {"INSERT": "[INS]", "UPDATE": "[UPD]", "DELETE": "[DEL]"}
    for _, row in df_filtrado.iterrows():
        fecha = row.get("fecha_hora", "")
        op = row.get("operacion", "UNK")
        tabla = row.get("tabla_nombre", "unknown")
        user = row.get("usuario_bd", "unknown")
        op_name = {"I": "INSERT", "U": "UPDATE", "D": "DELETE"}.get(op, op)
        tag = OP_COLORS.get(op_name, "[???]")
        linea = f"[{fecha}] {tag} user={user} table={tabla}"
        old_val = row.get("valores_old", "")
        new_val = row.get("valores_new", "")
        if pd.notna(old_val) and str(old_val).strip() not in ["None", ""]:
            linea += f" | old={old_val}"
        if pd.notna(new_val) and str(new_val).strip() not in ["None", ""]:
            linea += f" | new={new_val}"
        log_lines.append(linea)
    if log_lines:
        st.code("\n".join(log_lines), language="log")
    else:
        st.info("Sin eventos en el rango seleccionado.")

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

@st.cache_data
def convert_df(df_to_convert):
    return df_to_convert.to_csv(index=False).encode("utf-8")

csv_data = convert_df(df_filtrado.drop(columns=["solo_fecha"]))
st.download_button(
    label="⬇  Exportar reporte CSV",
    data=csv_data,
    file_name="reporte_auditoria.csv",
    mime="text/csv",
)
