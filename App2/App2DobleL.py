import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.scraping import hacer_scraping
from utils.language import resumir_texto, extraer_claves

st.set_page_config(page_title="Resumen de noticias", layout="wide")
st.title("📰 Resumen automático de noticias")
st.write("Introduce la URL de un periódico o blog para generar el resumen del día.")

url = st.text_input("🌐 Introduce la URL")

# Inicializar session_state
if 'titulares' not in st.session_state:
    st.session_state.titulares = []
if 'resumen' not in st.session_state:
    st.session_state.resumen = ""
if 'claves' not in st.session_state:
    st.session_state.claves = []

if st.button("Analizar"):
    if not url:
        st.warning("Por favor, introduce una URL.")
    else:
        with st.spinner("🔍 Obteniendo noticias..."):
            try:
                titulares, texto = hacer_scraping(url)
            except Exception as e:
                st.error(f"Error al hacer scraping: {e}")
                titulares, texto = [], ""

        if not texto:
            st.error("No se pudo extraer contenido de la URL proporcionada.")
        else:
            # Guardar titulares, resumen y claves en session_state
            st.session_state.titulares = titulares
            st.session_state.resumen = resumir_texto(texto)
            st.session_state.claves = extraer_claves(texto)

# -----------------------------------
# Carrusel automático de titulares
# -----------------------------------
st.subheader("🗞️ Titulares")
titulares = st.session_state.titulares

if titulares:
    # Cuenta de refresco para el carrusel
    count = st_autorefresh(interval=3000, limit=None, key="carousel")
    index = count % len(titulares)
    st.markdown(f"### {titulares[index]}")
else:
    st.write("⚠️ No se encontraron titulares.")

# -----------------------------------
# Resumen (fijo)
# -----------------------------------
st.subheader("📄 Resumen del día")
st.write(st.session_state.resumen or "⚠️ No hay resumen disponible.")

# -----------------------------------
# Ideas clave (fijas)
# -----------------------------------
st.subheader("🧠 Ideas clave")
if st.session_state.claves:
    for clave in st.session_state.claves:
        st.write("🔹", clave)
else:
    st.write("⚠️ No hay ideas clave disponibles.")