import streamlit as st
import pandas as pd
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.styles import GLOBAL_CSS, page_header, section_title

st.set_page_config(page_title="Análisis CSV — AuditDB", layout="wide", page_icon="📂")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if not st.session_state.get('autenticado', False):
    st.markdown("""<div style="text-align:center; padding:3rem; color:#475569;">
        <div style="font-size:2rem; margin-bottom:1rem;">🔒</div>
        <p>Acceso denegado. <a href="/" style="color:#3b82f6;">Inicia sesión</a></p>
    </div>""", unsafe_allow_html=True)
    st.stop()

page_header("📂", "Análisis de Logs CSV", "Carga reportes históricos sin necesidad de conexión activa")

# ===== DESCARGA DE EJEMPLOS =====
section_title("Archivos de ejemplo")
ex1, ex2 = st.columns(2)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

for col, fname, label in [
    (ex1, "reporte_auditar_prueba.csv", "Ejemplo 1 — PostgreSQL"),
    (ex2, "reporte_auditar_prueba_2.csv", "Ejemplo 2 — MySQL"),
]:
    fpath = os.path.join(DATA_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            datos = f.read()
        with col:
            st.markdown(f"""
            <div style="background:#141d35; border:1px solid #1e2d4d; border-radius:10px;
                        padding:1rem 1.25rem; margin-bottom:0.25rem;">
                <div style="font-size:0.8rem; font-weight:600; color:#94a3b8; margin-bottom:0.5rem;">📄 {label}</div>
            """, unsafe_allow_html=True)
            st.download_button(
                label=f"⬇  Descargar {fname}",
                data=datos,
                file_name=fname,
                mime="text/csv",
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ===== UPLOADER =====
section_title("Cargar archivo")
archivo_subido = st.file_uploader(
    "Arrastra un archivo CSV o haz clic para seleccionar",
    type=["csv"],
    help="Formatos soportados: CSV con columnas de auditoría estándar (fecha_hora, tabla_nombre, operacion, usuario_bd...)"
)

if archivo_subido is None:
    st.markdown("""
    <div style="text-align:center; padding:2.5rem; border:1px dashed #1e2d4d; border-radius:12px; margin-top:0.5rem;">
        <div style="font-size:2rem; margin-bottom:0.75rem;">📁</div>
        <p style="color:#475569; font-size:0.875rem; margin:0;">Sube un CSV para comenzar el análisis</p>
    </div>
    """, unsafe_allow_html=True)

if archivo_subido is not None:
    try:
        df_externo = pd.read_csv(archivo_subido)

        if 'fecha_hora' in df_externo.columns:
            df_externo['fecha_hora'] = pd.to_datetime(df_externo['fecha_hora'], errors='coerce')
            df_externo['solo_fecha'] = df_externo['fecha_hora'].dt.date

        # Banner de éxito
        st.markdown(f"""
        <div style="background:#10b98115; border:1px solid #10b98140; border-left:3px solid #10b981;
                    border-radius:8px; padding:0.75rem 1.25rem; margin:0.75rem 0; font-size:0.875rem;">
             <strong style="color:#10b981;">Archivo cargado correctamente</strong> — 
            <span style="color:#94a3b8;">{archivo_subido.name}</span>
        </div>
        """, unsafe_allow_html=True)

        # KPIs de carga
        k1, k2 = st.columns(2)
        with k1:
            st.metric("Filas cargadas", f"{len(df_externo):,}")
        with k2:
            st.metric("Columnas detectadas", len(df_externo.columns))

        st.markdown("<hr>", unsafe_allow_html=True)

        # ===== FILTROS SIDEBAR =====
        st.sidebar.markdown("""
        <div style="padding:0.75rem 0; border-bottom:1px solid #1e2d4d; margin-bottom:0.75rem;">
            <span style="font-size:0.7rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#475569;">
                Filtros del CSV
            </span>
        </div>
        """, unsafe_allow_html=True)
        df_filtrado_csv = df_externo.copy()

        if 'solo_fecha' in df_externo.columns:
            fechas_validas = df_externo['solo_fecha'].dropna()
            if not fechas_validas.empty:
                fecha_min = fechas_validas.min()
                fecha_max = fechas_validas.max()
                if fecha_min == fecha_max:
                    fechas_seleccionadas = st.sidebar.date_input("Rango de fechas", value=fecha_min)
                    rango_inicio, rango_fin = fechas_seleccionadas, fechas_seleccionadas
                else:
                    fechas_seleccionadas = st.sidebar.date_input("Rango de fechas", value=[fecha_min, fecha_max])
                    if isinstance(fechas_seleccionadas, (tuple, list)) and len(fechas_seleccionadas) == 2:
                        rango_inicio, rango_fin = fechas_seleccionadas
                    else:
                        rango_inicio = rango_fin = fechas_seleccionadas if not isinstance(fechas_seleccionadas, (tuple, list)) else fechas_seleccionadas[0]
                df_filtrado_csv = df_filtrado_csv[(df_filtrado_csv["solo_fecha"] >= rango_inicio) & (df_filtrado_csv["solo_fecha"] <= rango_fin)]

        if 'usuario_bd' in df_externo.columns:
            usuarios_disponibles = sorted(df_externo["usuario_bd"].dropna().astype(str).unique().tolist())
            usuarios_seleccionados = st.sidebar.multiselect("Usuario BD", options=usuarios_disponibles, default=usuarios_disponibles)
            df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["usuario_bd"].astype(str).isin(usuarios_seleccionados)]

        if 'tabla_nombre' in df_externo.columns:
            tablas_disponibles = sorted(df_externo["tabla_nombre"].dropna().astype(str).unique().tolist())
            tablas_seleccionadas = st.sidebar.multiselect("Tabla", options=tablas_disponibles, default=tablas_disponibles)
            df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["tabla_nombre"].astype(str).isin(tablas_seleccionadas)]

        if 'operacion' in df_externo.columns:
            operaciones_disponibles = sorted(df_externo["operacion"].dropna().astype(str).unique().tolist())
            operaciones_seleccionadas = st.sidebar.multiselect("Operación", options=operaciones_disponibles, default=operaciones_disponibles)
            df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["operacion"].astype(str).isin(operaciones_seleccionadas)]

        # ===== RESUMEN FILTRADO =====
        section_title("Resumen filtrado")
        s1, s2, s3 = st.columns(3)

        with s1:
            st.metric("Registros mostrados", f"{len(df_filtrado_csv):,}")

        if 'operacion' in df_filtrado_csv.columns:
            with s2:
                ic = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'I'])
                uc = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'U'])
                dc = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'D'])
                st.markdown(f"""
                <div style="background:#141d35; border:1px solid #1e2d4d; border-radius:10px; padding:1rem 1.25rem;">
                    <div style="font-size:0.68rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#475569; margin-bottom:0.5rem;">Desglose de operaciones</div>
                    <div style="display:flex; gap:0.75rem; font-family:'JetBrains Mono',monospace; font-size:0.9rem; font-weight:600;">
                        <span style="color:#10b981;">I: {ic}</span>
                        <span style="color:#3b82f6;">U: {uc}</span>
                        <span style="color:#ef4444;">D: {dc}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if 'tabla_nombre' in df_filtrado_csv.columns:
            with s3:
                st.metric("Tablas afectadas", df_filtrado_csv['tabla_nombre'].nunique())

        st.markdown("<hr>", unsafe_allow_html=True)

        # ===== TABLA DE DATOS =====
        section_title("Datos del archivo")
        columnas_mostrar = [col for col in df_filtrado_csv.columns if col != 'solo_fecha']
        st.dataframe(df_filtrado_csv[columnas_mostrar], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
