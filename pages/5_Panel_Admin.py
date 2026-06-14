import streamlit as st
import sqlite3
import pandas as pd
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.styles import GLOBAL_CSS, page_header, section_title

st.set_page_config(page_title="Panel Admin — AuditDB", layout="wide", page_icon="")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if not st.session_state.get("autenticado", False):
    st.markdown("""<div style="text-align:center; padding:3rem; color:#475569;">
        <div style="font-size:2rem; margin-bottom:1rem;"></div>
        <p>Acceso denegado. <a href="/" style="color:#3b82f6;">Inicia sesión</a></p>
    </div>""", unsafe_allow_html=True)
    st.stop()

if st.session_state.get("rol") != "admin":
    st.markdown("""
    <div style="text-align:center; padding:3rem;">
        <div style="font-size:2.5rem; margin-bottom:1rem;"></div>
        <h3 style="color:#ef4444; margin:0;">Acceso restringido</h3>
        <p style="color:#475569; font-size:0.875rem; margin-top:0.5rem;">Esta sección es exclusiva para administradores del sistema.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

page_header("O", "Panel de Administración", "Gestión de usuarios, accesos y métricas del sistema")

db_path = "saas_admin.db"

@st.cache_data(ttl=5)
def get_admin_data():
    conn = sqlite3.connect(db_path)
    df_usuarios = pd.read_sql_query("SELECT id, username, rol FROM usuarios", conn)
    df_accesos = pd.read_sql_query("SELECT id, username, fecha_hora FROM registro_accesos ORDER BY fecha_hora DESC", conn)
    try:
        df_conexiones = pd.read_sql_query("SELECT id, username, alias, motor FROM conexiones_guardadas ORDER BY id DESC", conn)
    except Exception:
        df_conexiones = pd.DataFrame(columns=["id", "username", "alias", "motor"])
    conn.close()
    return df_usuarios, df_accesos, df_conexiones

df_usuarios, df_accesos, df_conexiones = get_admin_data()

# ===== KPIs =====
section_title("Métricas del sistema")
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Usuarios registrados", len(df_usuarios))
with k2:
    st.metric("Inicios de sesión", len(df_accesos))
with k3:
    admins = len(df_usuarios[df_usuarios["rol"] == "admin"])
    st.metric("Administradores", admins)
with k4:
    st.metric("Conexiones BD guardadas", len(df_conexiones))

st.markdown("<hr>", unsafe_allow_html=True)

# ===== USUARIOS Y ACCESOS =====
section_title("Usuarios y actividad de accesos")
col_usr, col_acc = st.columns([1, 1.5])

with col_usr:
    st.markdown("""
    <div style="background:#141d35; border:1px solid #1e2d4d; border-radius:10px; overflow:hidden;">
        <div style="padding:0.75rem 1rem; border-bottom:1px solid #1e2d4d; background:#0f1628;">
            <span style="font-size:0.7rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#475569;">Usuarios del sistema</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(df_usuarios, use_container_width=True, hide_index=True)

with col_acc:
    st.markdown("""
    <div style="background:#141d35; border:1px solid #1e2d4d; border-radius:10px; overflow:hidden;">
        <div style="padding:0.75rem 1rem; border-bottom:1px solid #1e2d4d; background:#0f1628;">
            <span style="font-size:0.7rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#475569;">Historial de accesos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(df_accesos, use_container_width=True, hide_index=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    act1, act2 = st.columns(2)
    with act1:
        csv_data = df_accesos.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Exportar historial CSV",
            data=csv_data,
            file_name='historial_accesos.csv',
            mime='text/csv',
            use_container_width=True
        )
    with act2:
        if st.button(" Vaciar historial", use_container_width=True, type="secondary"):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM registro_accesos")
                conn.commit()
                conn.close()
                get_admin_data.clear()
                st.success("Historial vaciado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("<hr>", unsafe_allow_html=True)

# ===== CONEXIONES =====
section_title("Conexiones de clientes")
col_log, col_chart = st.columns([2, 1])

with col_log:
    st.markdown("""
    <div style="background:#141d35; border:1px solid #1e2d4d; border-radius:10px; overflow:hidden;">
        <div style="padding:0.75rem 1rem; border-bottom:1px solid #1e2d4d; background:#0f1628;">
            <span style="font-size:0.7rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#475569;">Registro de conexiones a BD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(df_conexiones, use_container_width=True, hide_index=True)

with col_chart:
    st.markdown("""
    <div style="background:#141d35; border:1px solid #1e2d4d; border-radius:10px; overflow:hidden; margin-bottom:0.5rem;">
        <div style="padding:0.75rem 1rem; border-bottom:1px solid #1e2d4d; background:#0f1628;">
            <span style="font-size:0.7rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#475569;">Uso por motor de BD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if not df_conexiones.empty:
        motor_counts = df_conexiones["motor"].value_counts()
        MOTOR_COLORS_FULL = {
            "PostgreSQL": "#336791", "MySQL": "#f29111",
            "SQLite": "#00aff4", "MongoDB": "#10aa50"
        }
        st.bar_chart(motor_counts, color="#3b82f6")

        # Tabla de distribución visual
        for motor, count in motor_counts.items():
            color = MOTOR_COLORS_FULL.get(motor, "#3b82f6")
            pct = int((count / motor_counts.sum()) * 100)
            st.markdown(f"""
            <div style="margin-bottom:0.4rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:3px;">
                    <span style="color:#94a3b8; font-weight:600;">{motor}</span>
                    <span style="color:{color}; font-weight:700; font-family:'JetBrains Mono',monospace;">{count}</span>
                </div>
                <div style="height:4px; background:#1e2d4d; border-radius:2px; overflow:hidden;">
                    <div style="height:100%; width:{pct}%; background:{color}; border-radius:2px; transition:width 0.3s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:2rem; color:#334155;">
            <div style="font-size:1.5rem; margin-bottom:0.5rem;"></div>
            <p style="font-size:0.825rem; margin:0;">Sin conexiones registradas aún</p>
        </div>
        """, unsafe_allow_html=True)

# ===== GESTIÓN DE USUARIOS =====
st.markdown("<hr>", unsafe_allow_html=True)
section_title("Gestión de usuarios", accent=True)

with st.expander("➕ Crear nuevo usuario"):
    with st.form("form_new_user"):
        nu_col1, nu_col2, nu_col3 = st.columns(3)
        with nu_col1:
            new_username = st.text_input("Nombre de usuario", placeholder="nuevo_usuario")
        with nu_col2:
            new_password = st.text_input("Contraseña temporal", type="password", placeholder="••••••••")
        with nu_col3:
            new_rol = st.selectbox("Rol", ["cliente", "admin"])
        
        create_btn = st.form_submit_button("Crear usuario →", type="primary")
        if create_btn:
            if not new_username or not new_password:
                st.error("Completa todos los campos.")
            else:
                import hashlib
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    hashed = hashlib.sha256(new_password.encode()).hexdigest()
                    cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", (new_username, hashed, new_rol))
                    conn.commit()
                    conn.close()
                    get_admin_data.clear()
                    st.success(f"Usuario **{new_username}** creado con rol **{new_rol}**.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Ese nombre de usuario ya existe.")
                except Exception as e:
                    st.error(f"Error: {e}")

with st.expander(" Eliminar usuario"):
    usuarios_eliminables = [u for u in df_usuarios["username"].tolist() if u != st.session_state.get("usuario_actual")]
    if usuarios_eliminables:
        del_user = st.selectbox("Selecciona el usuario a eliminar", usuarios_eliminables)
        if st.button(f"Eliminar a {del_user}", type="secondary"):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM usuarios WHERE username = ?", (del_user,))
                conn.commit()
                conn.close()
                get_admin_data.clear()
                st.success(f"Usuario **{del_user}** eliminado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("No hay otros usuarios para eliminar.")
