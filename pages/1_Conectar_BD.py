import streamlit as st
import os, sys, json, sqlite3
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.styles import GLOBAL_CSS, page_header, section_title

st.set_page_config(page_title="Conectar BD — AuditDB", layout="wide", page_icon="🔌")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if not st.session_state.get("autenticado", False):
    st.markdown("""
    <div style="text-align:center; padding:3rem; color:#475569;">
        <div style="font-size:2rem; margin-bottom:1rem;">🔒</div>
        <p>Acceso denegado. <a href="/" style="color:#3b82f6;">Inicia sesión</a></p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

page_header("🔌", "Conectar Base de Datos", "Configura la conexión para inyectar el motor de auditoría")

# ===== MOTOR BADGE HELPER =====
MOTOR_ICONS = {"PostgreSQL": "🐘", "MySQL": "🐬", "SQLite": "🗂️", "MongoDB": "🍃"}
MOTOR_COLORS = {"PostgreSQL": "#336791", "MySQL": "#f29111", "SQLite": "#00aff4", "MongoDB": "#10aa50"}

# ===== CONEXIONES GUARDADAS =====
usuario_actual = st.session_state.get("usuario_actual", "")
conexiones_guardadas = []
try:
    conn_admin = sqlite3.connect('saas_admin.db')
    cursor = conn_admin.cursor()
    cursor.execute("SELECT id, alias, motor, creds_json FROM conexiones_guardadas WHERE username = ?", (usuario_actual,))
    conexiones_guardadas = cursor.fetchall()
    conn_admin.close()
except Exception:
    pass

if conexiones_guardadas and not st.session_state.get("db_creds"):
    section_title("Conexiones guardadas")
    
    # Mostrar como cards
    cols = st.columns(min(len(conexiones_guardadas), 3))
    opciones = [{"id": 0, "label": "➕ Nueva conexión manual", "creds": None}]
    for row in conexiones_guardadas:
        try:
            creds_obj = json.loads(row[3])
            opciones.append({"id": row[0], "label": f"{row[1]} ({row[2]})", "motor": row[2], "creds": creds_obj})
        except:
            pass

    sel = st.selectbox(
        "Selecciona una conexión:",
        options=opciones,
        format_func=lambda x: x["label"],
        key="sel_conexion_guardada"
    )

    if sel["id"] != 0 and sel.get("creds"):
        motor_sel = sel.get("motor", "")
        icon = MOTOR_ICONS.get(motor_sel, "🗄️")
        color = MOTOR_COLORS.get(motor_sel, "#3b82f6")
        st.markdown(f"""
        <div style="background:#141d35; border:1px solid #1e2d4d; border-left:3px solid {color};
                    border-radius:10px; padding:1rem 1.25rem; margin:0.5rem 0; display:flex; align-items:center; gap:0.875rem;">
            <span style="font-size:1.4rem;">{icon}</span>
            <div>
                <div style="font-weight:600; color:#e2e8f0;">{sel['label']}</div>
                <div style="font-size:0.78rem; color:#475569; margin-top:2px;">Conexión guardada · Lista para usar</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Usar esta conexión →", type="primary"):
            st.session_state["db_creds"] = sel["creds"]
            st.success(f"Conectado usando: {sel['label']}")
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

# ===== FORMULARIO DE NUEVA CONEXIÓN =====
with st.expander("🔗 Configurar nueva conexión", expanded=not bool(st.session_state.get("db_creds"))):
    motor = st.selectbox(
        "Motor de base de datos",
        ["PostgreSQL", "MySQL", "SQLite", "MongoDB"],
        format_func=lambda m: f"{MOTOR_ICONS.get(m, '🗄️')}  {m}"
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    with st.form("form_conexion"):
        if motor in ["PostgreSQL", "MySQL"]:
            col1, col2 = st.columns(2)
            with col1:
                db_host = st.text_input("Host", value="localhost", placeholder="localhost")
                db_port = st.text_input("Puerto", value="5432" if motor == "PostgreSQL" else "3306")
                db_name = st.text_input("Base de datos", placeholder="mi_base_de_datos")
            with col2:
                db_user = st.text_input("Usuario", value="postgres" if motor == "PostgreSQL" else "root")
                db_password = st.text_input("Contraseña", type="password", placeholder="••••••••")
                
        elif motor == "SQLite":
            db_path = st.text_input(
                "Ruta del archivo SQLite",
                placeholder="/ruta/a/mi/base.db",
                value=st.session_state.get("sqlite_db_path", "")
            )
            
        elif motor == "MongoDB":
            mongo_uri = st.text_input("URI de conexión (opcional)", value="", placeholder="mongodb://user:pass@host:port/db")
            col1, col2 = st.columns(2)
            with col1:
                db_host = st.text_input("Host", value="localhost")
                db_port = st.text_input("Puerto", value="27017")
            with col2:
                db_name = st.text_input("Base de datos")
                db_user = st.text_input("Usuario (opcional)", value="")
                db_password = st.text_input("Contraseña (opcional)", type="password")

        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            guardar_nueva = st.checkbox("Guardar conexión", value=True)
        with col_g2:
            alias_nueva = st.text_input("Alias", value="Mi Base de Datos", placeholder="Ej: Producción Cliente X")

        submit_conn = st.form_submit_button("Probar y conectar →", use_container_width=True, type="primary")

        if submit_conn:
            try:
                creds = {}
                db_display_name = ""

                if motor == "PostgreSQL":
                    if not db_name: st.error("Ingresa el nombre de la base de datos."); st.stop()
                    import psycopg2
                    conn = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password)
                    conn.close()
                    creds = {"motor": motor, "host": db_host, "port": db_port, "dbname": db_name, "user": db_user, "password": db_password}
                    db_display_name = db_name

                elif motor == "MySQL":
                    if not db_name: st.error("Ingresa el nombre de la base de datos."); st.stop()
                    import pymysql
                    conn = pymysql.connect(host=db_host, port=int(db_port), database=db_name, user=db_user, password=db_password)
                    conn.close()
                    creds = {"motor": motor, "host": db_host, "port": int(db_port), "database": db_name, "user": db_user, "password": db_password}
                    db_display_name = db_name

                elif motor == "SQLite":
                    if not db_path: st.error("Ingresa la ruta del archivo."); st.stop()
                    import sqlite3 as _sq
                    conn = _sq.connect(db_path)
                    conn.close()
                    creds = {"motor": motor, "path": db_path}
                    db_display_name = db_path
                    st.session_state["sqlite_db_path"] = db_path

                elif motor == "MongoDB":
                    if not db_name: st.error("Ingresa el nombre de la base de datos."); st.stop()
                    from pymongo import MongoClient
                    uri = mongo_uri if mongo_uri else (
                        f"mongodb://{db_user}:{db_password}@{db_host}:{db_port}/"
                        if db_user and db_password else f"mongodb://{db_host}:{db_port}/"
                    )
                    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
                    client.server_info()
                    client.close()
                    creds = {"motor": motor, "uri": uri, "dbname": db_name}
                    db_display_name = db_name

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
                        st.warning(f"Conexión exitosa, pero no se pudo guardar en el historial: {ex}")

                st.session_state["db_creds"] = creds
                icon = MOTOR_ICONS.get(motor, "🗄️")
                st.success(f"{icon} Conectado a **{db_display_name}** ({motor})")
                st.rerun()
            except Exception as e:
                st.error(f"Error al conectar: {e}")

# ===== GESTIÓN POST-CONEXIÓN =====
if st.session_state.get("db_creds"):
    creds = st.session_state["db_creds"]
    motor_actual = creds.get("motor", "PostgreSQL")
    icon = MOTOR_ICONS.get(motor_actual, "🗄️")
    color = MOTOR_COLORS.get(motor_actual, "#3b82f6")

    st.markdown(f"""
    <div style="background:#141d35; border:1px solid #1e2d4d; border-left:3px solid {color};
                border-radius:10px; padding:0.875rem 1.25rem; margin:1rem 0;
                display:flex; align-items:center; gap:0.75rem;">
        <span style="font-size:1.25rem;">{icon}</span>
        <div>
            <span style="font-weight:600; color:#e2e8f0;">Motor activo: {motor_actual}</span>
            <span style="margin-left:0.75rem; background:{color}20; color:{color}; border:1px solid {color}40;
                         border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700;
                         letter-spacing:0.06em; text-transform:uppercase;">CONECTADO</span>
        </div>
        <div style="margin-left:auto;">
    """, unsafe_allow_html=True)

    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from utils.database import get_connection

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Instalar estructura base ---
    section_title("Instalar estructura base")
    if motor_actual in ["PostgreSQL", "MySQL", "SQLite"]:
        sql_filename = {"PostgreSQL": "core_auditoria.sql", "MySQL": "core_auditoria_mysql.sql", "SQLite": "core_auditoria_sqlite.sql"}[motor_actual]
        st.markdown(f"""
        <div style="background:#0f1628; border:1px solid #1e2d4d; border-radius:8px; padding:0.875rem 1rem; margin-bottom:0.75rem; font-size:0.825rem; color:#94a3b8;">
            Ejecutará <code style="background:#050810; padding:2px 6px; border-radius:4px; color:#06b6d4;">{sql_filename}</code> para crear la tabla <code style="background:#050810; padding:2px 6px; border-radius:4px; color:#06b6d4;">AUDITORIA_LOGS</code> y las funciones necesarias.
        </div>
        """, unsafe_allow_html=True)
        if st.button(f" Instalar motor de auditoría", type="primary"):
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
                st.success(f"Motor de auditoría instalado correctamente en {motor_actual}.")
            except FileNotFoundError:
                st.error(f"Archivo no encontrado: {sql_file_path}")
            except Exception as e:
                st.error(f"Error al instalar: {e}")

    elif motor_actual == "MongoDB":
        section_title("Instalar estructura base")
        st.info("En MongoDB no se requieren scripts SQL. La colección `AUDITORIA_LOGS` se crea automáticamente al iniciar el Change Stream.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Instrumentar tablas ---
    section_title("Instrumentar tablas / colecciones")
    st.markdown("<p style='font-size:0.825rem; color:#94a3b8; margin-bottom:0.75rem;'>Selecciona las tablas a las que deseas agregar triggers de auditoría.</p>", unsafe_allow_html=True)

    try:
        conn = get_connection()
        if motor_actual == "MongoDB":
            db_name = creds["dbname"]
            db = conn[db_name]
            tablas = [c for c in db.list_collection_names() if c != "AUDITORIA_LOGS"]
            conn.close()
        else:
            cur = conn.cursor()
            try:
                if motor_actual == "PostgreSQL":
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name!='auditoria_logs';")
                    tablas = [row[0] for row in cur.fetchall()]
                elif motor_actual == "MySQL":
                    cur.execute("SHOW TABLES;")
                    tablas = [row[0] for row in cur.fetchall() if row[0].lower() != 'auditoria_logs']
                elif motor_actual == "SQLite":
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='AUDITORIA_LOGS' AND name NOT LIKE 'sqlite_%';")
                    tablas = [row[0] for row in cur.fetchall()]
            finally:
                cur.close()
            conn.close()

        if tablas:
            tablas_seleccionadas = st.multiselect("Tablas disponibles:", tablas, placeholder="Selecciona una o más tablas...")
            btn_text = "▶  Iniciar Change Stream (MongoDB)" if motor_actual == "MongoDB" else "Inyectar triggers de auditoría"

            if st.button(btn_text, disabled=not tablas_seleccionadas):
                if tablas_seleccionadas:
                    try:
                        if motor_actual == "MongoDB":
                            import threading
                            from utils.mongo_auditor import start_mongo_audit
                            uri = creds["uri"]
                            dbname = creds["dbname"]
                            t = threading.Thread(target=start_mongo_audit, args=(uri, dbname, tablas_seleccionadas), daemon=True)
                            t.start()
                            st.success(f"Change Stream iniciado para: **{', '.join(tablas_seleccionadas)}**")
                        else:
                            conn = get_connection()
                            cur = conn.cursor()
                            try:
                                for tabla in tablas_seleccionadas:
                                    if motor_actual == "PostgreSQL":
                                        cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla} ON public.{tabla};")
                                        cur.execute(f"""
                                            CREATE TRIGGER trg_auditoria_{tabla}
                                            AFTER INSERT OR UPDATE OR DELETE ON public.{tabla}
                                            FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_generica();
                                        """)
                                    elif motor_actual == "MySQL":
                                        cur.execute(f"SHOW COLUMNS FROM {tabla};")
                                        columnas = [row[0] for row in cur.fetchall()]
                                        old_cols_str = ", ".join([f"'{col}', OLD.{col}" for col in columnas])
                                        new_cols_str = ", ".join([f"'{col}', NEW.{col}" for col in columnas])
                                        json_old = f"JSON_OBJECT({old_cols_str})"
                                        json_new = f"JSON_OBJECT({new_cols_str})"
                                        for op, val, name in [("D", json_old, "delete"), ("I", json_new, "insert"), ("U", None, "update")]:
                                            cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_{name};")
                                            if op == "U":
                                                cur.execute(f"CREATE TRIGGER trg_auditoria_{tabla}_update AFTER UPDATE ON {tabla} FOR EACH ROW INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, usuario_bd, valores_old, valores_new) VALUES ('{tabla}', 'U', USER(), {json_old}, {json_new});")
                                            elif op == "D":
                                                cur.execute(f"CREATE TRIGGER trg_auditoria_{tabla}_delete AFTER DELETE ON {tabla} FOR EACH ROW INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, usuario_bd, valores_old) VALUES ('{tabla}', 'D', USER(), {json_old});")
                                            else:
                                                cur.execute(f"CREATE TRIGGER trg_auditoria_{tabla}_insert AFTER INSERT ON {tabla} FOR EACH ROW INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, usuario_bd, valores_new) VALUES ('{tabla}', 'I', USER(), {json_new});")
                                    elif motor_actual == "SQLite":
                                        cur.execute(f"PRAGMA table_info({tabla});")
                                        columnas = [row[1] for row in cur.fetchall()]
                                        old_cols_str = ", ".join([f"'{col}', OLD.{col}" for col in columnas])
                                        new_cols_str = ", ".join([f"'{col}', NEW.{col}" for col in columnas])
                                        json_old = f"json_object({old_cols_str})"
                                        json_new = f"json_object({new_cols_str})"
                                        for suffix, body in [
                                            ("delete", f"INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, valores_old) VALUES ('{tabla}', 'D', {json_old});"),
                                            ("insert", f"INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, valores_new) VALUES ('{tabla}', 'I', {json_new});"),
                                            ("update", f"INSERT INTO AUDITORIA_LOGS (tabla_nombre, operacion, valores_old, valores_new) VALUES ('{tabla}', 'U', {json_old}, {json_new});"),
                                        ]:
                                            cur.execute(f"DROP TRIGGER IF EXISTS trg_auditoria_{tabla}_{suffix};")
                                            cur.execute(f"CREATE TRIGGER trg_auditoria_{tabla}_{suffix} AFTER {'DELETE' if suffix=='delete' else 'INSERT' if suffix=='insert' else 'UPDATE'} ON {tabla} FOR EACH ROW BEGIN {body} END;")
                                conn.commit()
                            finally:
                                cur.close()
                            conn.close()
                            st.success(f"Triggers inyectados en: **{', '.join(tablas_seleccionadas)}**")
                    except Exception as e:
                        st.error(f"Error al instrumentar: {e}")
        else:
            st.warning("No se encontraron tablas. Crea algunas primero o instala el motor de auditoría.")
    except Exception as e:
        st.error(f"Error al consultar tablas: {e}")
