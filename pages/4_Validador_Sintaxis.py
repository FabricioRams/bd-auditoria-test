import streamlit as st
import requests

if not st.session_state.get("autenticado", False):
    st.warning("Debes iniciar sesion para ver esta pagina.")
    st.stop()

st.title("Validador de Sintaxis SQL/NoSQL")
st.markdown("Verifica la sintaxis de tus consultas **SQL** y **MongoDB (NoSQL)** antes de ejecutarlas.")

query_input = st.text_area("Consulta a validar:", height=150, placeholder="Escribe tu consulta aquí... (Ej: SELECT * FROM usuarios;)")

col1, col2 = st.columns([1, 3])
with col1:
    tipo_input = st.selectbox("Tipo de consulta (Opcional)", ["Auto", "sql", "nosql"])
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    validar_btn = st.button("Validar Consulta", type="primary")

if validar_btn:
    if not query_input.strip():
        st.warning("Por favor, ingresa una consulta para validar.")
    else:
        payload = {
            "query": query_input
        }
        if tipo_input != "Auto":
            payload["tipo"] = tipo_input

        with st.spinner("Validando..."):
            try:
                response = requests.post(
                    "https://validador-per-production.up.railway.app/api/validar",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("valid"):
                        st.success("✅ ¡Consulta válida!")
                        st.info(f"**Dialecto detectado:** {data.get('dialect', 'N/A')} (Confianza: {data.get('confidence', 100)}%)")
                        
                        compatibles = data.get("compatible", [])
                        if compatibles:
                            st.write("**Compatible con motores SQL:**")
                            st.write(", ".join(compatibles))
                            
                        sugerencias = data.get("suggestions", [])
                        if sugerencias:
                            with st.expander("Detalles adicionales"):
                                for s in sugerencias:
                                    st.write(s)
                    else:
                        st.error("⚠️ La consulta tiene errores de sintaxis.")
                        
                        errores = data.get("errors", [])
                        for error in errores:
                            linea = error.get('line', '?')
                            columna = error.get('column', '?')
                            with st.expander(f"Error en línea {linea}, columna {columna}", expanded=True):
                                st.write(f"**Mensaje:** {error.get('message', 'N/A')}")
                                if error.get("fragment"):
                                    st.write(f"**Fragmento:** `{error.get('fragment')}`")
                                if error.get("suggestion"):
                                    st.write(f"**Sugerencia:** {error.get('suggestion')}")
                        
                        sugerencias_generales = data.get("suggestions", [])
                        if sugerencias_generales and not errores:
                            st.write("**Sugerencias:**")
                            for s in sugerencias_generales:
                                st.write(f"- {s}")
                                
                elif response.status_code == 400:
                    data = response.json()
                    st.error(f"Error en la petición: {data.get('error', {}).get('message', 'Request inválida')}")
                else:
                    st.error(f"Error inesperado del servidor (Código {response.status_code}).")
            except Exception as e:
                st.error(f"Error de conexión con el servicio de validación: {e}")
