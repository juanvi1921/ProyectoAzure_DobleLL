# -Leer una imagen con OCR
# -Analizar texto saliente con PLN idioma, tipo de texto ...
# -Clasificar fichero según idioma y tipo moviéndolo a una carpeta creada.

import streamlit as st
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from Utils import leer_texto_azure, detectar_idioma, analizar_sentimiento, clasificar_y_guardar

st.title("OCR + Análisis de Texto")

uploaded_file = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])

if uploaded_file:
    st.image(uploaded_file)

    # OCR
    texto = leer_texto_azure(uploaded_file)

    st.subheader("Texto detectado")
    st.write(texto)

    # NLP
    idioma = detectar_idioma(texto)
    sentimiento = analizar_sentimiento(texto)

    st.subheader("Resultados NLP")
    st.write(f"Idioma: {idioma}")
    st.write(f"Sentimiento: {sentimiento}")

    # Clasificación
    ruta = clasificar_y_guardar(uploaded_file, texto, idioma, sentimiento)

    st.success(f"Archivo guardado en: {ruta}")







