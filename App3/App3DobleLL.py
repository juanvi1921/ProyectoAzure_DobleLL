# -OCR leer matrícula de vehículos
# -Insertar en BBDD desde python
# Gestor de parking:
# Si estoy dentro:
# -Y quiero entrar: no me deja
# -Y quiero salir: me deja
# Si estoy fuera:
# -Y quiero entrar: me deja
# -Y quiero salir: no me deja

import streamlit as st
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from Utils import leer_matricula, gestionar_parking, despedida_tts

st.title("Gestor de Parking Inteligente con OCR y TTS")

uploaded_file = st.file_uploader("Sube imagen del coche", type=["png", "jpg", "jpeg"])
accion = st.selectbox("Acción", ["entrar", "salir"])

if uploaded_file:
    matricula = leer_matricula(uploaded_file)
    st.write("Matrícula detectada:", matricula)

    mensaje = gestionar_parking(matricula, accion)
    st.write(mensaje)

    audio_path = despedida_tts(matricula, f"{mensaje}. ¡Hasta luego!")
    st.audio(audio_path, format="audio/mp3")