import streamlit as st
import requests
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.styles import GLOBAL_CSS, page_header, section_title

st.set_page_config(page_title="Validador SQL/NoSQL — AuditDB", layout="wide", page_icon="🔬")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if not st.session_state.get("autenticado", False):
    st.markdown("""<div style="text-align:center; padding:3rem; color:#475569;">
        <div style="font-size:2rem; margin-bottom:1rem;"></div>
        <p>Acceso denegado. <a href="/" style="color:#3b82f6;">Inicia sesión</a></p>
    </div>""", unsafe_allow_html=True)
    st.stop()

page_header("O", "Validador de Sintaxis SQL/NoSQL", "Verifica consultas antes de ejecutarlas en producción")

# ===== EJEMPLOS RÁPIDOS =====
section_title("Ejemplos rápidos")
EJEMPLOS = {
    "SELECT básico": "SELECT id, nombre, email FROM usuarios WHERE activo = 1 ORDER BY nombre;",
    "INSERT": "INSERT INTO productos (nombre, precio, stock) VALUES ('Laptop', 1299.99, 50);",
    "UPDATE": "UPDATE clientes SET estado = 'activo', fecha_mod = NOW() WHERE id = 42;",
    "DELETE": "DELETE FROM logs WHERE fecha_hora < '2024-01-01' AND tipo = 'debug';",
    "JOIN complejo": "SELECT u.username, COUNT(a.id) as total_ops\nFROM usuarios u\nLEFT JOIN auditoria_logs a ON a.usuario_bd = u.username\nGROUP BY u.username\nORDER BY total_ops DESC;",
    "MongoDB NoSQL": '{"find": "usuarios", "filter": {"activo": true, "rol": "admin"}, "sort": {"creado": -1}}',
}

ej_cols = st.columns(3)
for i, (label, query) in enumerate(EJEMPLOS.items()):
    with ej_cols[i % 3]:
        if st.button(f" {label}", use_container_width=True, key=f"ej_{i}"):
            st.session_state["query_preload"] = query

# ===== EDITOR =====
st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
section_title("Editor de consulta")

preload = st.session_state.pop("query_preload", "")
query_input = st.text_area(
    "Consulta a validar",
    value=preload,
    height=180,
    placeholder="Escribe tu consulta SQL o MongoDB aquí...\n\nEj: SELECT * FROM usuarios WHERE activo = 1;",
    label_visibility="collapsed"
)

ctrl1, ctrl2, ctrl3 = st.columns([1.5, 2, 1.5])
with ctrl1:
    tipo_input = st.selectbox(
        "Tipo",
        ["Auto", "sql", "nosql"],
        format_func=lambda x: {"Auto": " Detección automática", "sql": " SQL", "nosql": " NoSQL (MongoDB)"}[x]
    )
with ctrl2:
    st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
    validar_btn = st.button("▶  Validar consulta", type="primary", use_container_width=True)
with ctrl3:
    st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
    limpiar_btn = st.button("  Limpiar", use_container_width=True)
    if limpiar_btn:
        st.session_state["query_preload"] = ""
        st.rerun()

# ===== VALIDACIÓN =====
if validar_btn:
    if not query_input.strip():
        st.warning("Escribe una consulta antes de validar.")
    else:
        payload = {"query": query_input}
        if tipo_input != "Auto":
            payload["tipo"] = tipo_input

        with st.spinner("Validando con el servicio externo..."):
            try:
                response = requests.post(
                    "https://validador-per-production.up.railway.app/api/validar",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("valid"):
                        st.markdown(f"""
                        <div style="background:#10b98115; border:1px solid #10b98140; border-left:3px solid #10b981;
                                    border-radius:10px; padding:1rem 1.25rem; margin:0.75rem 0;">
                            <div style="font-weight:700; color:#10b981; font-size:1rem; margin-bottom:0.4rem;">
                                 Consulta válida
                            </div>
                            <div style="font-size:0.825rem; color:#94a3b8;">
                                Dialecto detectado: <strong style="color:#e2e8f0;">{data.get('dialect', 'N/A')}</strong> 
                                &nbsp;·&nbsp; Confianza: <strong style="color:#e2e8f0;">{data.get('confidence', 100)}%</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        compatibles = data.get("compatible", [])
                        if compatibles:
                            section_title("Compatibilidad de motores")
                            mc = st.columns(len(compatibles))
                            MOTOR_ICONS = {"PostgreSQL": "🐘", "MySQL": "🐬", "SQLite": "🗂️", "MongoDB": "🍃"}
                            for i, motor in enumerate(compatibles):
                                with mc[i]:
                                    icon = MOTOR_ICONS.get(motor, "🗄️")
                                    st.markdown(f"""
                                    <div style="background:#141d35; border:1px solid #10b98140; border-radius:8px;
                                                padding:0.625rem 0.875rem; text-align:center; font-size:0.825rem;
                                                color:#10b981; font-weight:600;">
                                        {icon} {motor}
                                    </div>
                                    """, unsafe_allow_html=True)

                        sugerencias = data.get("suggestions", [])
                        if sugerencias:
                            with st.expander("💡 Sugerencias adicionales"):
                                for s in sugerencias:
                                    st.markdown(f"<p style='font-size:0.825rem; color:#94a3b8; margin:4px 0;'>• {s}</p>", unsafe_allow_html=True)

                    else:
                        st.markdown("""
                        <div style="background:#ef444415; border:1px solid #ef444440; border-left:3px solid #ef4444;
                                    border-radius:10px; padding:1rem 1.25rem; margin:0.75rem 0;">
                            <div style="font-weight:700; color:#ef4444; font-size:1rem;"> Errores de sintaxis detectados</div>
                        </div>
                        """, unsafe_allow_html=True)

                        errores = data.get("errors", [])
                        for error in errores:
                            linea = error.get('line', '?')
                            columna = error.get('column', '?')
                            with st.expander(f" Error — Línea {linea}, col. {columna}", expanded=True):
                                st.markdown(f"""
                                <div style="font-size:0.825rem; line-height:1.7;">
                                    <div><span style="color:#475569; font-weight:600; text-transform:uppercase; font-size:0.7rem; letter-spacing:0.06em;">Mensaje</span><br>
                                    <span style="color:#e2e8f0;">{error.get('message', 'N/A')}</span></div>
                                """, unsafe_allow_html=True)
                                if error.get("fragment"):
                                    st.markdown(f"""<div style="margin-top:0.5rem"><span style="color:#475569; font-weight:600; text-transform:uppercase; font-size:0.7rem; letter-spacing:0.06em;">Fragmento</span><br>
                                    <code style="background:#050810; padding:2px 8px; border-radius:4px; color:#ef4444;">{error.get('fragment')}</code></div>""", unsafe_allow_html=True)
                                if error.get("suggestion"):
                                    st.markdown(f"""<div style="margin-top:0.5rem"><span style="color:#475569; font-weight:600; text-transform:uppercase; font-size:0.7rem; letter-spacing:0.06em;">Sugerencia</span><br>
                                    <span style="color:#10b981;">→ {error.get('suggestion')}</span></div>""", unsafe_allow_html=True)
                                st.markdown("</div>", unsafe_allow_html=True)

                elif response.status_code == 400:
                    data = response.json()
                    st.error(f"Error en la petición: {data.get('error', {}).get('message', 'Request inválida')}")
                else:
                    st.error(f"Error inesperado del servidor (código {response.status_code}).")

            except Exception as e:
                st.error(f"Error de conexión con el servicio de validación: {e}")
