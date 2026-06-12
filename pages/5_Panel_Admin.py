import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Panel de Administración", layout="wide")

# 1. Verificación de Autenticación y Rol
if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal.")
    st.stop()

if st.session_state.get("rol") != "admin":
    st.error("🚫 Acceso denegado. Esta página es exclusiva para administradores.")
    st.stop()

st.title(" Panel de Administración")
st.markdown("Gestión de usuarios y métricas de acceso del sistema.")

# 2. Conectar a la base de datos interna saas_admin.db
db_path = "saas_admin.db"

@st.cache_data(ttl=5) # Cache pequeño para no saturar lecturas concurrentes
def get_admin_data():
    conn = sqlite3.connect(db_path)
    
    # Usuarios (excluyendo password)
    df_usuarios = pd.read_sql_query("SELECT id, username, rol FROM usuarios", conn)
    
    # Historial de accesos
    df_accesos = pd.read_sql_query("SELECT id, username, fecha_hora FROM registro_accesos ORDER BY fecha_hora DESC", conn)
    
    # Logs de conexiones de clientes
    try:
        df_conexiones = pd.read_sql_query("SELECT id, username, alias, motor FROM conexiones_guardadas ORDER BY id DESC", conn)
    except Exception:
        # Por si la tabla aún no existe (migración)
        df_conexiones = pd.DataFrame(columns=["id", "username", "alias", "motor"])
        
    conn.close()
    return df_usuarios, df_accesos, df_conexiones

df_usuarios, df_accesos, df_conexiones = get_admin_data()

# 3. Métricas Generales
st.subheader(" Métricas Generales")
col1, col2 = st.columns(2)
with col1:
    st.metric("Total de Usuarios Registrados", len(df_usuarios))
with col2:
    st.metric("Total de Inicios de Sesión", len(df_accesos))

st.markdown("---")

# 4. Tablas de Datos
col_usr, col_acc = st.columns(2)

with col_usr:
    st.subheader(" Usuarios del Sistema")
    st.dataframe(df_usuarios, use_container_width=True, hide_index=True)

with col_acc:
    st.subheader(" Historial de Accesos")
    st.dataframe(df_accesos, use_container_width=True, hide_index=True)
    
    # 5. Botones de acción para el historial
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # Descargar CSV
        csv_data = df_accesos.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=" Descargar Historial (CSV)",
            data=csv_data,
            file_name='historial_accesos.csv',
            mime='text/csv',
            use_container_width=True
        )
        
    with col_btn2:
        # Vaciar Historial
        if st.button(" Vaciar Historial", use_container_width=True, type="secondary"):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM registro_accesos")
                conn.commit()
                conn.close()
                st.success("Historial vaciado correctamente.")
                # Limpiamos el caché para reflejar los cambios inmediatamente
                get_admin_data.clear() 
                st.rerun()
            except Exception as e:
                st.error(f"Error al vaciar el historial: {e}")

st.markdown("---")
st.subheader(" Registros de Conexión de Clientes")

col_con_log, col_con_chart = st.columns([2, 1])

with col_con_log:
    st.markdown("#### Historial de Conexiones a BD")
    st.dataframe(df_conexiones, use_container_width=True, hide_index=True)

with col_con_chart:
    st.markdown("#### Uso por Motor de BD")
    if not df_conexiones.empty:
        motor_counts = df_conexiones["motor"].value_counts()
        st.bar_chart(motor_counts, color="#3b82f6")
    else:
        st.info("Aún no hay conexiones registradas.")
