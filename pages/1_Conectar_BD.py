import streamlit as st
import os

st.set_page_config(page_title="Conectar a BD Cliente", layout="wide")

# 1. Validar autenticación
if not st.session_state.get("autenticado", False):
    st.warning("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal.")
    st.stop()

import sqlite3
import json

st.title("🔌 Conectar a Base de Datos del Cliente")
st.markdown("Configura la conexión a la base de datos de tu cliente para inyectar remotamente el motor de auditoría.")

# --- Cargar conexiones guardadas ---
usuario_actual = st.session_state.get("usuario_actual", "")
conexiones_guardadas = []
try:
    conn_admin = sqlite3.connect('saas_admin.db')
    cursor = conn_admin.cursor()
    cursor.execute("SELECT id, alias, motor, creds_json FROM conexiones_guardadas WHERE username = ?", (usuario_actual,))
    conexiones_guardadas = cursor.fetchall()
    conn_admin.close()
except Exception as e:
    pass

if conexiones_guardadas and not st.session_state.get("db_creds"):
    st.subheader("📂 Conexiones Guardadas")
    opciones = [{"id": 0, "label": "--- Nueva Conexión Manual ---", "creds": None}]
    for row in conexiones_guardadas:
        try:
            creds_obj = json.loads(row[3])
            opciones.append({"id": row[0], "label": f"{row[1]} ({row[2]})", "creds": creds_obj})
        except:
            pass
            
    seleccion = st.selectbox(
        "Selecciona una conexión guardada:",
        options=opciones,
        format_func=lambda x: x["label"]
    )
    
    if seleccion["id"] != 0:
        if st.button("🚀 Conectar con conexión seleccionada", type="primary", use_container_width=True):
            st.session_state["db_creds"] = seleccion["creds"]
            st.success(f"✅ Conectado usando la conexión guardada: {seleccion['label']}")
            st.rerun()
    st.markdown("---")

# 2. Formulario de Conexión Manual
with st.expander("🔗 Configurar Credenciales de Conexión", expanded=not bool(st.session_state.get("db_creds"))):
    motor = st.selectbox("Motor de Base de Datos", ["PostgreSQL", "MySQL", "SQLite", "MongoDB"])
    
    with st.form("form_conexion"):
        if motor in ["PostgreSQL", "MySQL"]:
            col1, col2 = st.columns(2)
            with col1:
                db_host = st.text_input("Host", value="localhost")
                db_port = st.text_input("Puerto", value="5432" if motor == "PostgreSQL" else "3306")
                db_name = st.text_input("Nombre de la Base de Datos")
            with col2:
                db_user = st.text_input("Usuario", value="postgres" if motor == "PostgreSQL" else "root")
                db_password = st.text_input("Contraseña", type="password")
        elif motor == "SQLite":
            db_path = st.text_input("Ruta del archivo SQLite", placeholder="Ej: C:/rutas/a/mi/base.db", value=st.session_state.get("sqlite_db_path", ""))
        elif motor == "MongoDB":
            mongo_uri = st.text_input("URI de Conexión (opcional, ignora Host/Puerto/Credenciales si se provee)", value="")
            col1, col2 = st.columns(2)
            with col1:
                db_host = st.text_input("Host", value="localhost")
                db_port = st.text_input("Puerto", value="27017")
            with col2:
                db_name = st.text_input("Nombre de la Base de Datos")
                db_user = st.text_input("Usuario (opcional)", value="")
                db_password = st.text_input("Contraseña (opcional)", type="password")
        
        guardar_nueva = st.checkbox("💾 Guardar esta conexión para el futuro", value=True)
        alias_nueva = st.text_input("Alias para guardar (ej. 'Producción Cliente X')", value="Mi Base de Datos")
        
        submit_conn = st.form_submit_button("Probar Conexión y Guardar", use_container_width=True)
        
        if submit_conn:
            try:
                creds = {}
                db_display_name = ""
                
                if motor == "PostgreSQL":
                    if not db_name: st.error("Por favor ingresa el nombre de la base de datos."); st.stop()
                    import psycopg2
                    conn = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password)
                    conn.close()
                    creds = {"motor": motor, "host": db_host, "port": db_port, "dbname": db_name, "user": db_user, "password": db_password}
                    db_display_name = db_name
                    
                elif motor == "MySQL":
                    if not db_name: st.error("Por favor ingresa el nombre de la base de datos."); st.stop()
                    import pymysql
                    conn = pymysql.connect(host=db_host, port=int(db_port), database=db_name, user=db_user, password=db_password)
                    conn.close()
                    creds = {"motor": motor, "host": db_host, "port": int(db_port), "database": db_name, "user": db_user, "password": db_password}
                    db_display_name = db_name
                    
                elif motor == "SQLite":
                    if not db_path: st.error("Por favor ingresa la ruta del archivo."); st.stop()
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    conn.close()
                    creds = {"motor": motor, "path": db_path}
                    db_display_name = db_path
                    st.session_state["sqlite_db_path"] = db_path
                    
                elif motor == "MongoDB":
                    if not db_name: st.error("Por favor ingresa el nombre de la base de datos."); st.stop()
                    from pymongo import MongoClient
                    if mongo_uri:
                        uri = mongo_uri
                    else:
                        if db_user and db_password:
                            uri = f"mongodb://{db_user}:{db_password}@{db_host}:{db_port}/"
                        else:
                            uri = f"mongodb://{db_host}:{db_port}/"
                    
                    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
                    client.server_info() # Provocar conexión para validar
                    client.close()
                    creds = {"motor": motor, "uri": uri, "dbname": db_name}
                    db_display_name = db_name
                
                # Guardar conexión en DB local si el check está marcado
                if guardar_nueva:
                    try:
                        conn_admin = sqlite3.connect('saas_admin.db')
                        cursor = conn_admin.cursor()
                        cursor.execute(
                            "INSERT INTO conexiones_guardadas (username, alias, motor, creds_json) VALUES (?, ?, ?, ?)",
                            (usuario_actual, alias_nueva, motor, json.dumps(creds))
                        )
                        conn_admin.commit()
                        conn_admin.close()
                    except Exception as ex:
                        st.warning(f"La conexión fue exitosa pero no se pudo guardar en el historial: {ex}")
                
                st.session_state["db_creds"] = creds
                st.success(f"✅ Conexión exitosa a la base de datos '{db_display_name}' ({motor}).")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al conectar: {e}")

# Si hay credenciales, procedemos al resto de funcionalidades
if st.session_state.get("db_creds"):
    st.markdown("---")
    
    st.header("⚙️ Gestión del Motor de Auditoría")
    
    # Importar función genérica de conexión
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from utils.database import get_connection

    motor_actual = st.session_state["db_creds"].get("motor", "PostgreSQL")
    st.info(f"Conectado actualmente al motor: **{motor_actual}**")

    if motor_actual in ["PostgreSQL", "MySQL", "SQLite"]:
        st.subheader("1. Instalar Estructura Base")
        
        sql_filename = {
            "PostgreSQL": "core_auditoria.sql",
            "MySQL": "core_auditoria_mysql.sql",
            "SQLite": "core_auditoria_sqlite.sql"
        }[motor_actual]
        
        st.write(f"Esta acción ejecutará `{sql_filename}` para crear la tabla `AUDITORIA_LOGS` (y funciones si aplica) en la base de datos conectada.")
        
        if st.button("🚀 Instalar Motor de Auditoría", type="primary"):
            sql_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_scripts", sql_filename)
                
            try:
                with open(sql_file_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()
                    
                conn = get_connection()
                try:
                    if motor_actual == "SQLite":
                        conn.executescript(sql_script)
                        conn.commit()
                    else:
                        cur = conn.cursor()
                        try:
                            if motor_actual == "MySQL":
                                # Separar por ; y ejecutar
                                for statement in sql_script.split(';'):
                                    if statement.strip():
                                        cur.execute(statement)
                            else:
                                cur.execute(sql_script)
                            conn.commit()
                        finally:
                            cur.close()
                finally:
                    conn.close()
                st.success(f"✅ Motor de auditoría ({motor_actual}) instalado correctamente.")
            except FileNotFoundError:
                st.error(f"❌ No se encontró el archivo de núcleo: {sql_file_path}")
            except Exception as e:
                st.error(f"❌ Error al instalar el motor: {e}")

        st.markdown("---")
    elif motor_actual == "MongoDB":
        st.subheader("1. Instalar Estructura Base")
        st.info("ℹ️ En MongoDB no es necesario inyectar scripts SQL. La colección `AUDITORIA_LOGS` se creará automáticamente cuando se inicie el Change Stream.")
        st.markdown("---")
        
    st.subheader("2. Instrumentar Tablas / Colecciones")
    st.write("Selecciona las tablas o colecciones a las que deseas agregarles el trigger de auditoría o Change Stream.")
    
    try:
        conn = get_connection()
        if motor_actual == "MongoDB":
            db_name = st.session_state["db_creds"]["dbname"]
            db = conn[db_name]
            tablas = [c for c in db.list_collection_names() if c != "AUDITORIA_LOGS"]
            conn.close()
        else:
            cur = conn.cursor()
            try:
                if motor_actual == "PostgreSQL":
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                          AND table_type = 'BASE TABLE'
                          AND table_name != 'auditoria_logs';
                    """)
                    tablas = [row[0] for row in cur.fetchall()]
                elif motor_actual == "MySQL":
                    cur.execute("SHOW TABLES;")
                    tablas = [row[0] for row in cur.fetchall() if row[0].lower() != 'auditoria_logs']
                elif motor_actual == "SQLite":
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'AUDITORIA_LOGS' AND name NOT LIKE 'sqlite_%';")
                    tablas = [row[0] for row in cur.fetchall()]
            finally:
                cur.close()
            conn.close()
        
        if tablas:
            tablas_seleccionadas = st.multiselect("Tablas/Colecciones disponibles:", tablas)
            
            btn_text = "🚀 Iniciar Auditoría (Change Stream)" if motor_actual == "MongoDB" else "💉 Inyectar Triggers de Auditoría"
            
            if st.button(btn_text) and tablas_seleccionadas:
                try:
                    if motor_actual == "MongoDB":
                        import threading
                        from utils.mongo_auditor import start_mongo_audit
                        
                        uri = st.session_state["db_creds"]["uri"]
                        dbname = st.session_state["db_creds"]["dbname"]
                        
                        t = threading.Thread(target=start_mongo_audit, args=(uri, dbname, tablas_seleccionadas), daemon=True)
                        t.start()
                        
                        st.success(f"✅ Change Stream iniciado en segundo plano para: **{', '.join(tablas_seleccionadas)}**")
                    else:
                        conn = get_connection()
                        cur = conn.cursor()
                        try:
                            for tabla in tablas_seleccionadas:
                                if motor_actual == "PostgreSQL":
                                    cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla} ON public.{tabla};")
                                    cur.execute(f"""
                                        CREATE TRIGGER trg_auditoria_{tabla}
                                        AFTER INSERT OR UPDATE OR DELETE
                                        ON public.{tabla}
                                        FOR EACH ROW
                                        EXECUTE FUNCTION public.fn_auditoria_generica();
                                    """)
                                elif motor_actual == "MySQL":
                                    cur.execute(f"SHOW COLUMNS FROM {tabla};")
                                    columnas = [row[0] for row in cur.fetchall()]
                                    
                                    # Construir listas de strings de forma limpia para evitar SyntaxError por backslash
                                    old_cols_str = ", ".join([f"'{col}', OLD.{col}" for col in columnas])
                                    new_cols_str = ", ".join([f"'{col}', NEW.{col}" for col in columnas])
                                    
                                    json_old = f"JSON_OBJECT({old_cols_str})"
                                    json_new = f"JSON_OBJECT({new_cols_str})"
                                    
                                    # Delete
                                    cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_delete;")
                                    cur.execute(f"""
                                        CREATE TRIGGER trg_auditoria_{tabla}_delete
                                        AFTER DELETE ON {tabla} FOR EACH ROW
                                        INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, usuario_bd, valores_old)
                                        VALUES ('{tabla}', 'D', USER(), {json_old});
                                    """)
                                    # Insert
                                    cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_insert;")
                                    cur.execute(f"""
                                        CREATE TRIGGER trg_auditoria_{tabla}_insert
                                        AFTER INSERT ON {tabla} FOR EACH ROW
                                        INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, usuario_bd, valores_new)
                                        VALUES ('{tabla}', 'I', USER(), {json_new});
                                    """)
                                    # Update
                                    cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_update;")
                                    cur.execute(f"""
                                        CREATE TRIGGER trg_auditoria_{tabla}_update
                                        AFTER UPDATE ON {tabla} FOR EACH ROW
                                        INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, usuario_bd, valores_old, valores_new)
                                        VALUES ('{tabla}', 'U', USER(), {json_old}, {json_new});
                                    """)
                                elif motor_actual == "SQLite":
                                    cur.execute(f"PRAGMA table_info({tabla});")
                                    columnas = [row[1] for row in cur.fetchall()]
                                    
                                    # Construir listas de strings de forma limpia para evitar SyntaxError por backslash
                                    old_cols_str = ", ".join([f"'{col}', OLD.{col}" for col in columnas])
                                    new_cols_str = ", ".join([f"'{col}', NEW.{col}" for col in columnas])
                                    
                                    json_old = f"json_object({old_cols_str})"
                                    json_new = f"json_object({new_cols_str})"
                                    
                                    # Delete
                                    cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_delete;")
                                    cur.execute(f"""
                                        CREATE TRIGGER trg_auditoria_{tabla}_delete
                                        AFTER DELETE ON {tabla} FOR EACH ROW
                                        BEGIN
                                            INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, valores_old)
                                            VALUES ('{tabla}', 'D', {json_old});
                                        END;
                                    """)
                                    # Insert
                                    cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_insert;")
                                    cur.execute(f"""
                                        CREATE TRIGGER trg_auditoria_{tabla}_insert
                                        AFTER INSERT ON {tabla} FOR EACH ROW
                                        BEGIN
                                            INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, valores_new)
                                            VALUES ('{tabla}', 'I', {json_new});
                                        END;
                                    """)
                                    # Update
                                    cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_update;")
                                    cur.execute(f"""
                                        CREATE TRIGGER trg_auditoria_{tabla}_update
                                        AFTER UPDATE ON {tabla} FOR EACH ROW
                                        BEGIN
                                            INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, valores_old, valores_new)
                                            VALUES ('{tabla}', 'U', {json_old}, {json_new});
                                        END;
                                    """)
                            conn.commit()
                        finally:
                            cur.close()
                        conn.close()
                                
                        st.success(f"✅ Triggers inyectados correctamente en: **{', '.join(tablas_seleccionadas)}**")
                except Exception as e:
                    st.error(f"❌ Error al instrumentar tablas/colecciones: {e}")
            elif not tablas_seleccionadas:
                st.info("Selecciona al menos una tabla/colección de la lista.")
        else:
            st.warning("No se encontraron tablas/colecciones base para instrumentar. ¡Crea algunas primero!")
            
    except Exception as e:
        st.error(f"❌ Error al consultar las tablas/colecciones: {e}")
