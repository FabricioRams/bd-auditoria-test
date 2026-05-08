import streamlit as st
import psycopg2
import os

st.set_page_config(page_title="Conectar a BD Cliente", layout="wide")

# 1. Validar autenticación
if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal.")
    st.stop()

st.title("🔌 Conectar a Base de Datos del Cliente (SaaS)")
st.markdown("Configura la conexión a la base de datos de tu cliente para inyectar remotamente el motor de auditoría.")

# 2. Formulario de Conexión
with st.expander("🔗 Configurar Credenciales de Conexión", expanded=not bool(st.session_state.get("db_creds"))):
    with st.form("form_conexion"):
        col1, col2 = st.columns(2)
        with col1:
            db_host = st.text_input("Host", value="localhost")
            db_port = st.text_input("Puerto", value="5432")
            db_name = st.text_input("Nombre de la Base de Datos")
        with col2:
            db_user = st.text_input("Usuario", value="postgres")
            db_password = st.text_input("Contraseña", type="password")
        
        submit_conn = st.form_submit_button("Probar Conexión y Guardar", use_container_width=True)
        
        if submit_conn:
            if not db_name:
                st.error("Por favor ingresa el nombre de la base de datos.")
            else:
                try:
                    # Intentar conexión
                    conn = psycopg2.connect(
                        host=db_host,
                        port=db_port,
                        dbname=db_name,
                        user=db_user,
                        password=db_password
                    )
                    conn.close()
                    
                    st.session_state["db_creds"] = {
                        "host": db_host,
                        "port": db_port,
                        "dbname": db_name,
                        "user": db_user,
                        "password": db_password
                    }
                    st.success(f"✅ Conexión exitosa a la base de datos '{db_name}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al conectar: {e}")

# Si hay credenciales, procedemos al resto de funcionalidades
if st.session_state.get("db_creds"):
    st.markdown("---")
    
    st.header("⚙️ Gestión del Motor de Auditoría")
    
    # Función helper para obtener conexión actual
    def get_current_conn():
        return psycopg2.connect(**st.session_state["db_creds"])

    # 3. Instalar Motor de Auditoría
    st.subheader("1. Instalar Estructura Base")
    st.write("Esta acción ejecutará `core_auditoria.sql` para crear la tabla `AUDITORIA_LOGS` y la función genérica `fn_auditoria_generica()` en la base de datos conectada.")
    
    if st.button("🚀 Instalar Motor de Auditoría", type="primary"):
        sql_file_path = "core_auditoria.sql"
        if not os.path.exists(sql_file_path):
            # Fallback en caso de que streamlit no se haya ejecutado desde la raíz
            sql_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core_auditoria.sql")
            
        try:
            with open(sql_file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
                
            with get_current_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_script)
            st.success("✅ Motor de auditoría instalado correctamente. Ya puedes comenzar a instrumentar las tablas.")
        except FileNotFoundError:
            st.error(f"❌ No se encontró el archivo de núcleo: {sql_file_path}")
        except Exception as e:
            st.error(f"❌ Error al instalar el motor: {e}")

    st.markdown("---")
    
    # 4. Listar tablas e Inyectar Triggers
    st.subheader("2. Instrumentar Tablas")
    st.write("Selecciona las tablas del esquema `public` a las que deseas agregarles el trigger de auditoría.")
    
    try:
        with get_current_conn() as conn:
            with conn.cursor() as cur:
                # Consultar tablas existentes en public, descartando la tabla de logs
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_type = 'BASE TABLE'
                      AND table_name != 'auditoria_logs';
                """)
                tablas = [row[0] for row in cur.fetchall()]
        
        if tablas:
            tablas_seleccionadas = st.multiselect("Tablas disponibles (esquema public):", tablas)
            
            if st.button("💉 Inyectar Triggers de Auditoría") and tablas_seleccionadas:
                try:
                    with get_current_conn() as conn:
                        with conn.cursor() as cur:
                            for tabla in tablas_seleccionadas:
                                # 1. Borrar trigger anterior si existe
                                cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla} ON public.{tabla};")
                                
                                # 2. Crear el trigger
                                cur.execute(f"""
                                    CREATE TRIGGER trg_auditoria_{tabla}
                                    AFTER INSERT OR UPDATE OR DELETE
                                    ON public.{tabla}
                                    FOR EACH ROW
                                    EXECUTE FUNCTION public.fn_auditoria_generica();
                                """)
                    st.success(f"✅ Triggers inyectados correctamente en: **{', '.join(tablas_seleccionadas)}**")
                except Exception as e:
                    st.error(f"❌ Error al inyectar triggers: {e}")
            elif not tablas_seleccionadas:
                st.info("Selecciona al menos una tabla de la lista para inyectar los triggers.")
        else:
            st.warning("No se encontraron tablas base en el esquema `public` (excluyendo la de logs). ¡Crea algunas tablas primero!")
            
    except Exception as e:
        st.error(f"❌ Error al consultar las tablas: {e}")
