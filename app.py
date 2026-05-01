import streamlit as st

st.set_page_config(page_title="Auditoría de Base de Datos", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; color: #0f172a;'>
        Panel de Auditoría PostgreSQL
    </h1>
    """,
    unsafe_allow_html=True,
)

# Inicializar estado global de sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "df_externo" not in st.session_state:
    st.session_state["df_externo"] = None


def verificar_credenciales(usuario, contrasena):
    usuarios_permitidos = {
        "fabricio": "admin123",
        "rodrigo": "dev456",
        "auditor_externo": "upt2026",
    }
    return usuario in usuarios_permitidos and usuarios_permitidos[usuario] == contrasena


if not st.session_state["autenticado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<h2 style='text-align: center;'>Acceso Restringido</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sistema de Auditoría de Base de Datos</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            usuario_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit_btn = st.form_submit_button("Ingresar al Dashboard", use_container_width=True)

            if submit_btn:
                if verificar_credenciales(usuario_input, password_input):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = usuario_input
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Acceso denegado.")

    st.stop()

st.success(f"Bienvenido, {st.session_state.get('usuario_actual', 'usuario')}.")
st.info("Usa los accesos directos de abajo o el menú lateral de Streamlit para abrir Monitoreo en Vivo o Cargador CSV.")

st.markdown("### Accesos directos")
col1, col2 = st.columns(2)

with col1:
    st.button(
        "Ir a Monitoreo en Vivo",
        use_container_width=True,
        on_click=lambda: st.switch_page("Monitoreo Vivo")
    )

with col2:
    st.button(
        "Ir a Cargador CSV",
        use_container_width=True,
        on_click=lambda: st.switch_page("Cargador CSV")
    )
