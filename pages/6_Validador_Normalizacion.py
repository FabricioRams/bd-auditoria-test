import streamlit as st
import requests
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.styles import GLOBAL_CSS, page_header, section_title

st.set_page_config(page_title="Validador de Normalización — AuditDB", layout="wide", page_icon="📐")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if not st.session_state.get("autenticado", False):
    st.markdown("""<div style="text-align:center; padding:3rem; color:#475569;">
        <div style="font-size:2rem; margin-bottom:1rem;"></div>
        <p>Acceso denegado. <a href="/" style="color:#3b82f6;">Inicia sesión</a></p>
    </div>""", unsafe_allow_html=True)
    st.stop()

page_header("📐", "Validador de Normalización", "Diagnóstico automático de formas normales (1FN, 2FN, 3FN) con IA")

# ===== EJEMPLOS RÁPIDOS =====
section_title("Ejemplos rápidos (Haz clic para probar)")
EJEMPLOS = {
    "Violación 1FN": """CREATE TABLE ordenes (
    orden_id INT PRIMARY KEY,
    cliente_nombre VARCHAR(100),
    producto_1 VARCHAR(50),
    producto_2 VARCHAR(50)
);""",
    "Violación 2FN": """CREATE TABLE detalle_orden (
    orden_id INT,
    producto_id INT,
    producto_nombre VARCHAR(100),
    cantidad INT,
    PRIMARY KEY(orden_id, producto_id)
);""",
    "Violación 3FN": """CREATE TABLE clientes (
    id INT PRIMARY KEY,
    nombre VARCHAR(100),
    ciudad VARCHAR(50),
    region VARCHAR(50)
);""",
    "Modelo Ideal (3FN)": """CREATE TABLE empleados (
    emp_id INT PRIMARY KEY,
    nombre VARCHAR(100),
    depto_id INT
);

CREATE TABLE departamentos (
    depto_id INT PRIMARY KEY,
    depto_nombre VARCHAR(100)
);"""
}

ej_cols = st.columns(4)
for i, (label, query) in enumerate(EJEMPLOS.items()):
    with ej_cols[i % 4]:
        if st.button(f" {label}", use_container_width=True, key=f"ej_norm_{i}"):
            st.session_state["query_input_norm"] = query

# ===== EDITOR =====
st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
section_title("Esquema SQL a Evaluar")

query_input = st.text_area(
    "Consulta a validar",
    key="query_input_norm",
    height=220,
    placeholder="Pega las sentencias CREATE TABLE de tu esquema aquí...\n\nEj: CREATE TABLE clientes ( id INT PRIMARY KEY, nombre VARCHAR(100) );",
    label_visibility="collapsed"
)

ctrl1, ctrl2, ctrl3 = st.columns([1.5, 2, 1.5])
with ctrl1:
    st.write("") # Placeholder
with ctrl2:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    validar_btn = st.button("▶  Evaluar Normalización", type="primary", use_container_width=True)
with ctrl3:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    limpiar_btn = st.button("  Limpiar", use_container_width=True)
    if limpiar_btn:
        st.session_state["query_input_norm"] = ""
        st.rerun()

# ===== VALIDACIÓN =====
if validar_btn:
    if not query_input.strip():
        st.warning("Pega un esquema SQL antes de evaluar.")
    else:
        payload = {"sql": query_input}

        with st.spinner("Ejecutando motor heurístico DataQuest..."):
            try:
                response = requests.post(
                    "https://app-dataquest-web-api.azurewebsites.net/api/normalizacion",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("success"):
                        nivel_actual = data.get("nivel_actual", "Desconocido")
                        color_nivel = "#10b981" if nivel_actual == "3FN" else ("#f59e0b" if nivel_actual == "2FN" else "#ef4444")
                        
                        st.markdown(f"""
                        <div style="background:{color_nivel}15; border:1px solid {color_nivel}40; border-left:3px solid {color_nivel};
                                    border-radius:10px; padding:1.25rem; margin:0.75rem 0; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <div style="font-weight:700; color:{color_nivel}; font-size:1.1rem; margin-bottom:0.2rem;">
                                    Diagnóstico Exitoso
                                </div>
                                <div style="font-size:0.9rem; color:#e2e8f0;">
                                    {data.get("resumen", "Resumen no disponible")}
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:0.7rem; text-transform:uppercase; font-weight:700; color:#94a3b8; letter-spacing:1px;">Nivel Detectado</div>
                                <div style="font-size:2rem; font-weight:800; color:{color_nivel}; font-family:'JetBrains Mono', monospace;">{nivel_actual}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Mostrar Violaciones
                        def mostrar_violaciones(violaciones, titulo, color):
                            if violaciones:
                                st.markdown(f"""
                                <div style="margin-top:1.5rem; margin-bottom:0.5rem; font-weight:600; color:{color}; font-size:1rem; border-bottom: 1px solid {color}40; padding-bottom:0.3rem;">
                                    🚨 Violaciones a {titulo}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                for v in violaciones:
                                    tabla = v.get("tabla", "?")
                                    mensaje = v.get("mensaje", "")
                                    
                                    with st.expander(f"Tabla afectada: {tabla}"):
                                        st.markdown(f"""<div style="font-size:0.875rem; color:#e2e8f0; margin-bottom:0.5rem;">{mensaje}</div>""", unsafe_allow_html=True)
                                        
                                        cols = st.columns(2)
                                        with cols[0]:
                                            if "determinante" in v:
                                                st.markdown(f"""<span style="color:#94a3b8; font-size:0.75rem;">Determinante:</span> <code style="color:#3b82f6;">{v.get('determinante')}</code>""", unsafe_allow_html=True)
                                        with cols[1]:
                                            if "dependientes" in v:
                                                deps = ", ".join(v.get('dependientes', []))
                                                st.markdown(f"""<span style="color:#94a3b8; font-size:0.75rem;">Dependientes:</span> <code style="color:#ef4444;">{deps}</code>""", unsafe_allow_html=True)
                        
                        mostrar_violaciones(data.get("violaciones_1fn", []), "Primera Forma Normal (1FN)", "#ef4444")
                        mostrar_violaciones(data.get("violaciones_2fn", []), "Segunda Forma Normal (2FN)", "#f59e0b")
                        mostrar_violaciones(data.get("violaciones_3fn", []), "Tercera Forma Normal (3FN)", "#facc15")
                        
                        mejoras = data.get("mejoras_opcionales", [])
                        if mejoras:
                            st.markdown("""
                            <div style="margin-top:1.5rem; margin-bottom:0.5rem; font-weight:600; color:#3b82f6; font-size:1rem; border-bottom: 1px solid #3b82f640; padding-bottom:0.3rem;">
                                💡 Mejoras Opcionales
                            </div>
                            """, unsafe_allow_html=True)
                            for m in mejoras:
                                st.info(f"**Tabla `{m.get('tabla', '?')}` - {m.get('tipo', 'Mejora')}**: {m.get('mensaje', '')}")

                    else:
                        st.error(f"El validador devolvió un error (pero con status 200): {data.get('error', {}).get('message', data)}")

                elif response.status_code in [400, 500]:
                    data = response.json()
                    st.markdown("""
                    <div style="background:#ef444415; border:1px solid #ef444440; border-left:3px solid #ef4444;
                                border-radius:10px; padding:1rem 1.25rem; margin:0.75rem 0;">
                        <div style="font-weight:700; color:#ef4444; font-size:1rem;">Error de Análisis</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.error(f"{data.get('error', {}).get('message', 'No se pudo procesar el esquema.')}")
                else:
                    st.error(f"Error inesperado del servidor (código {response.status_code}).")

            except requests.exceptions.RequestException as e:
                st.error(f"Error de red contactando la API DataQuest: {e}")
