import streamlit as st
import pandas as pd

# Validar si el usuario está logueado (protección de la página)
if not st.session_state.get('autenticado', False):
    st.error(" Acceso denegado. Por favor, inicia sesión en la página principal.")
    st.stop()

st.markdown("###  Análisis de Logs Externos")
st.info("Sube un reporte histórico de PostgreSQL o MySQL en formato .csv para analizarlo sin conexión a la base de datos.")

# ==========================================
# DESCARGAS DE EJEMPLOS
# ==========================================
st.markdown("** Descargar Archivos de Ejemplo**")
col1, col2 = st.columns(2)

# Archivo de ejemplo 1
try:
    with open("reporte_auditar_prueba.csv", "r", encoding="utf-8") as f:
        datos_ejemplo1 = f.read()
    with col1:
        st.download_button(
            label=" Descargar: reporte_auditar_prueba.csv",
            data=datos_ejemplo1,
            file_name="reporte_auditar_prueba.csv",
            mime="text/csv"
        )
except FileNotFoundError:
    pass

# Archivo de ejemplo 2
try:
    with open("reporte_auditar_prueba_2.csv", "r", encoding="utf-8") as f:
        datos_ejemplo2 = f.read()
    with col2:
        st.download_button(
            label=" Descargar: reporte_auditar_prueba_2.csv",
            data=datos_ejemplo2,
            file_name="reporte_auditar_prueba_2.csv",
            mime="text/csv"
        )
except FileNotFoundError:
    pass

st.markdown("---")

# Widget para subir archivo
archivo_subido = st.file_uploader("Selecciona un archivo CSV", type=["csv"])

if archivo_subido is not None:
    try:
        # Leer el archivo nuevo
        df_externo = pd.read_csv(archivo_subido)
        
        # Preprocesar fechas de forma segura
        if 'fecha_hora' in df_externo.columns:
            df_externo['fecha_hora'] = pd.to_datetime(df_externo['fecha_hora'], errors='coerce')
            df_externo['solo_fecha'] = df_externo['fecha_hora'].dt.date
            
        st.success(" ¡Archivo procesado correctamente!")
        
        # Resumen general
        col_a, col_b = st.columns(2)
        col_a.metric("Total de Filas Originales", len(df_externo))
        col_b.metric("Columnas Detectadas", len(df_externo.columns))
        
        # ==========================================
        # FILTROS DINÁMICOS (Sin memoria residual)
        # ==========================================
        st.sidebar.header(" Filtros del CSV")
        df_filtrado_csv = df_externo.copy()
        
        # 1. Filtro de Fechas
        if 'solo_fecha' in df_externo.columns:
            fechas_validas = df_externo['solo_fecha'].dropna()
            if not fechas_validas.empty:
                fecha_min = fechas_validas.min()
                fecha_max = fechas_validas.max()
                
                # Al quitar el parámetro "key", evitamos el bug de caché
                if fecha_min == fecha_max:
                    fechas_seleccionadas = st.sidebar.date_input("Rango de Fechas", value=fecha_min)
                    rango_inicio, rango_fin = fechas_seleccionadas, fechas_seleccionadas
                else:
                    fechas_seleccionadas = st.sidebar.date_input("Rango de Fechas", value=[fecha_min, fecha_max])
                    if isinstance(fechas_seleccionadas, tuple) or isinstance(fechas_seleccionadas, list):
                        if len(fechas_seleccionadas) == 2:
                            rango_inicio, rango_fin = fechas_seleccionadas
                        else:
                            rango_inicio, rango_fin = fechas_seleccionadas[0], fechas_seleccionadas[0]
                    else:
                        rango_inicio, rango_fin = fechas_seleccionadas, fechas_seleccionadas
                        
                df_filtrado_csv = df_filtrado_csv[
                    (df_filtrado_csv["solo_fecha"] >= rango_inicio) &
                    (df_filtrado_csv["solo_fecha"] <= rango_fin)
                ]
                
        # 2. Filtro de Usuarios
        if 'usuario_bd' in df_externo.columns:
            usuarios_disponibles = sorted(df_externo["usuario_bd"].dropna().astype(str).unique().tolist())
            usuarios_seleccionados = st.sidebar.multiselect("Usuario de BD", options=usuarios_disponibles, default=usuarios_disponibles)
            df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["usuario_bd"].astype(str).isin(usuarios_seleccionados)]
            
        # 3. Filtro de Tablas
        if 'tabla_nombre' in df_externo.columns:
            tablas_disponibles = sorted(df_externo["tabla_nombre"].dropna().astype(str).unique().tolist())
            tablas_seleccionadas = st.sidebar.multiselect("Tabla", options=tablas_disponibles, default=tablas_disponibles)
            df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["tabla_nombre"].astype(str).isin(tablas_seleccionadas)]
            
        # 4. Filtro de Operación
        if 'operacion' in df_externo.columns:
            operaciones_disponibles = sorted(df_externo["operacion"].dropna().astype(str).unique().tolist())
            operaciones_seleccionadas = st.sidebar.multiselect("Operación", options=operaciones_disponibles, default=operaciones_disponibles)
            df_filtrado_csv = df_filtrado_csv[df_filtrado_csv["operacion"].astype(str).isin(operaciones_seleccionadas)]

        st.markdown("---")
        
        # ==========================================
        # RENDERIZADO DE RESULTADOS
        # ==========================================
        st.markdown("###  Resumen Filtrado")
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            st.metric("Registros Mostrados", len(df_filtrado_csv))
            
        if 'operacion' in df_filtrado_csv.columns:
            with stat_col2:
                insert_count = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'I'])
                update_count = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'U'])
                delete_count = len(df_filtrado_csv[df_filtrado_csv['operacion'] == 'D'])
                st.metric("Total de Cambios", f"I:{insert_count} U:{update_count} D:{delete_count}")
                
        if 'tabla_nombre' in df_filtrado_csv.columns:
            with stat_col3:
                tablas_count = df_filtrado_csv['tabla_nombre'].nunique()
                st.metric("Tablas Afectadas", tablas_count)

        st.markdown("---")
        st.markdown("###  Datos del CSV")
        
        # Mostramos la tabla interactiva sin la columna auxiliar
        columnas_mostrar = [col for col in df_filtrado_csv.columns if col != 'solo_fecha']
        st.dataframe(df_filtrado_csv[columnas_mostrar], use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al analizar el archivo: {e}")