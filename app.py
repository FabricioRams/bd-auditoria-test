import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(page_title="Auditoría de Base de Datos", layout="wide")

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    conn = sqlite3.connect('saas_admin.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_accesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conexiones_guardadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            alias TEXT NOT NULL,
            motor TEXT NOT NULL,
            creds_json TEXT NOT NULL
        )
    ''')
    
    # Insert default admin if table is empty
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            ('admin', hash_password('admin123'), 'admin')
        )
    
    conn.commit()
    conn.close()

init_db()

st.markdown(
    """
    <h1 style='text-align: center; color: #0f172a;'>
        Panel de Auditoría Multi-Motor
    </h1>
    """,
    unsafe_allow_html=True,
)

# Inicializar estado global de sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "df_externo" not in st.session_state:
    st.session_state["df_externo"] = None

if not st.session_state["autenticado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<h2 style='text-align: center;'>Inicia Sesión o Registrate</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sistema de Auditoría de Base de Datos SaaS</p>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab1:
            with st.form("login_form"):
                usuario_input = st.text_input("Usuario")
                password_input = st.text_input("Contraseña", type="password")
                submit_btn = st.form_submit_button("Ingresar al Dashboard", use_container_width=True)

                if submit_btn:
                    if not usuario_input or not password_input:
                        st.error("Por favor completa todos los campos.")
                    else:
                        conn = sqlite3.connect('saas_admin.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT password, rol FROM usuarios WHERE username = ?", (usuario_input,))
                        result = cursor.fetchone()
                        
                        if result and result[0] == hash_password(password_input):
                            rol = result[1]
                            
                            # Registrar acceso
                            cursor.execute(
                                "INSERT INTO registro_accesos (username, fecha_hora) VALUES (?, ?)", 
                                (usuario_input, datetime.now())
                            )
                            conn.commit()
                            conn.close()
                            
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_actual"] = usuario_input
                            st.session_state["rol"] = rol
                            
                            # Redirección automática a la página de conexión
                            st.switch_page("pages/3_Conectar_BD.py")
                        else:
                            conn.close()
                            st.error("Credenciales incorrectas. Acceso denegado.")
                            
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("Nuevo Usuario")
                new_pass = st.text_input("Contraseña", type="password")
                new_pass_confirm = st.text_input("Confirmar Contraseña", type="password")
                register_btn = st.form_submit_button("Registrarse", use_container_width=True)
                
                if register_btn:
                    if not new_user or not new_pass or not new_pass_confirm:
                        st.error("Por favor completa todos los campos.")
                    elif new_pass != new_pass_confirm:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        conn = sqlite3.connect('saas_admin.db')
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                                (new_user, hash_password(new_pass), 'cliente')
                            )
                            conn.commit()
                            st.success("Usuario registrado exitosamente. Ahora puedes iniciar sesión en la otra pestaña.")
                        except sqlite3.IntegrityError:
                            st.error("El usuario ya existe. Por favor elige otro username.")
                        finally:
                            conn.close()
    
    st.stop()

# --- MENSAJE DE BIENVENIDA AL ENTRAR ---
st.success(f"✅ Bienvenido, {st.session_state.get('usuario_actual', 'usuario')} (Rol: {st.session_state.get('rol', 'cliente')}).")
st.info("👈 Usa el menú lateral izquierdo para navegar entre las opciones del sistema.")