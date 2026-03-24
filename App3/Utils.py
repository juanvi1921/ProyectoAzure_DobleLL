import os
import re
import time
import sqlite3
from dotenv import load_dotenv
import requests
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import azure.cognitiveservices.speech as speechsdk

# Cargar credenciales
load_dotenv("credentials.env")

# --- Azure Vision ---
VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
VISION_KEY = os.getenv("VISION_KEY")

client_VI = ComputerVisionClient(
    endpoint=VISION_ENDPOINT,
    credentials=CognitiveServicesCredentials(VISION_KEY)
)

# --- Azure TTS ---
STT_KEY = os.getenv("STT_KEY")
STT_ENDPOINT = os.getenv("STT_ENDPOINT")  # región de tu recurso Speech
speech_config = speechsdk.SpeechConfig(subscription=STT_KEY, endpoint=STT_ENDPOINT)

# --- Base de datos SQLite ---
DB_PATH = os.path.join(os.path.dirname(__file__), "parking.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS parking (
    matricula TEXT PRIMARY KEY,
    estado TEXT
)
""")
conn.commit()

# --- OCR ---
def leer_matricula(imagen):
    """OCR usando Azure Computer Vision"""
    read_response = client_VI.read_in_stream(imagen, raw=True)
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Espera activa hasta obtener resultado
    while True:
        result = client_VI.get_read_result(operation_id)
        if result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    matricula = ""
    if result.status == "succeeded":
        for page in result.analyze_result.read_results:
            for line in page.lines:
                matricula += line.text + " "
    matricula = re.sub(r'[^A-Za-z0-9]', '', matricula).upper()
    return matricula

# --- Gestión parking ---
def get_estado(matricula):
    cursor.execute("SELECT estado FROM parking WHERE matricula=?", (matricula,))
    row = cursor.fetchone()
    if row:
        return row[0]
    return "fuera"

def actualizar_estado(matricula, nuevo_estado):
    if get_estado(matricula) == "fuera" and nuevo_estado == "fuera":
        return False
    if get_estado(matricula) == "dentro" and nuevo_estado == "dentro":
        return False
    cursor.execute("INSERT OR REPLACE INTO parking (matricula, estado) VALUES (?, ?)", (matricula, nuevo_estado))
    conn.commit()
    return True

def gestionar_parking(matricula, accion):
    estado = get_estado(matricula)
    mensaje = ""
    if estado == "dentro" and accion == "entrar":
        mensaje = "Ya estás dentro"
    elif estado == "dentro" and accion == "salir":
        actualizar_estado(matricula, "fuera")
        mensaje = "Salida permitida"
    elif estado == "fuera" and accion == "entrar":
        actualizar_estado(matricula, "dentro")
        mensaje = "Entrada permitida"
    else:
        mensaje = "No puedes salir si no has entrado"
    return mensaje

# --- Detección país de matrícula (simple regex) ---
def detectar_pais_matricula(matricula):
    if re.match(r'^\d{4}[A-Z]{3}$', matricula):
        return "es"
    elif re.match(r'^[A-Z]{1,3}[A-Z]{1,2}\d{1,4}$', matricula):
        return "de"
    elif re.match(r'^[A-Z]{2}\d{2}\s?[A-Z]{3}$', matricula):
        return "en"
    else:
        return "en"

# --- Text-to-Speech usando SDK oficial ---
def despedida_tts(matricula, mensaje):
    pais = detectar_pais_matricula(matricula)
    voces = {"es": "es-ES-AlvaroNeural", "en": "en-GB-RyanNeural", "de": "de-DE-KatjaNeural"}
    voz = voces.get(pais, "en-GB-RyanNeural")

    speech_config.speech_synthesis_voice_name = voz
    audio_path = os.path.join(os.path.dirname(__file__), "despedida.mp3")
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_path)

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text(mensaje)

    return audio_path