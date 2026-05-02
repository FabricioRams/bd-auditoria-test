import streamlit as st
import pandas as pd

# Validar si el usuario está logueado (protección de la página)
if not st.session_state.get('autenticado', False):
    st.error(" Acceso denegado. Por favor, inicia sesión en la página principal.")
    st.stop()

st.markdown("###  Análisis de Logs Externos")
st.info("Sube un reporte histórico de PostgreSQL o MySQL en formato .csv para analizarlo sin conexión a la base de datos.")
# --- NUEVO: SECCIÓN DESPLEGABLE CON EJEMPLOS ---
with st.expander("💡 ¿No tienes un archivo? Descarga datos de prueba"):
    st.write("Usa estos archivos generados automáticamente para probar cómo el sistema se adapta a diferentes formatos sin que la aplicación colapse.")
    
    col_ej1, col_ej2 = st.columns(2)
    
    # Datos del Ejemplo 1 (Formato Clásico de Ventas)
    csv_clasico = """log_id,fecha_hora,usuario_bd,tabla_nombre,operacion,valores_new
1,2026-05-01 10:00:00,admin_inventario,public.productos,I,"{""nombre"": ""Laptop"", ""stock"": 50}"
2,2026-05-01 10:15:00,app_ventas,public.ventas,I,"{""total"": 1500}"
3,2026-05-02 11:00:00,admin_inventario,public.productos,U,"{""stock"": 49}"
4,2026-05-02 12:30:00,app_ventas,public.ventas,I,"{""total"": 80.50}"
"""
    with col_ej1:
        st.download_button(
            label="⬇️ Descargar Log de Ventas (Clásico)",
            data=csv_clasico.encode('utf-8'),
            file_name="ejemplo_ventas.csv",
            mime="text/csv"
        )
        
    # Datos del Ejemplo 2 (Formato Universidad)
    csv_uni = """log_id,fecha_hora,usuario_bd,tabla_nombre,operacion,detalles
101,2026-05-01 08:00:00,admin_upt,public.libros,I,"{""libro"": ""Patrones de Diseño (GoF)""}"
102,2026-05-01 09:15:22,sistema_lab,public.prestamos,I,"{""estudiante"": ""Arocutipa"", ""equipo"": ""Router Cisco""}"
103,2026-05-02 09:30:10,sistema_lab,public.prestamos,I,"{""estudiante"": ""Perez"", ""equipo"": ""Switch 2960""}"
104,2026-05-03 14:10:00,admin_upt,public.libros,D,"{""libro"": ""Arquitectura Monolítica""}"
105,2026-05-04 18:30:00,sistema_lab,public.prestamos,I,"{""estudiante"": ""Colque"", ""equipo"": ""Cable Consola""}"
"""
    with col_ej2:
        st.download_button(
            label="⬇️ Descargar Log Universidad (Alternativo)",
            data=csv_uni.encode('utf-8'),
            file_name="ejemplo_universidad.csv",
            mime="text/csv"
        )
# ------------------------------------------------

# Aquí continúa tu código original:
archivo_subido = st.file_uploader("Selecciona un archivo CSV", type=["csv"])
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