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
    read_response = client_VI.read_in_stream(imagen, raw=True)
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    while True:
        result = client_VI.get_read_result(operation_id)
        if result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    texto_total = ""
    if result.status == "succeeded":
        for page in result.analyze_result.read_results:
            for line in page.lines:
                texto_total += line.text + " "

    matricula = extraer_matricula_valida(texto_total)

    return matricula if matricula else "NO_DETECTADA"

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


# --- Detección país de matrícula (simple regex) ---
import re

def detectar_pais_matricula(matricula):
    matricula = matricula.upper().strip()

    if re.match(r'^\d{4}\s?[BCDFGHJKLMNPRSTVWXYZ]{3}$', matricula):
        return "es"
    elif re.match(r'^[A-Z]{1,3}\s?[A-Z]{1,2}\s?\d{1,4}$', matricula):
        return "de"
    elif re.match(r'^[A-Z]{2}\d{2}\s?[A-Z]{3}$', matricula):
        return "uk"
    elif re.match(r'^[A-Z]{2}-?\d{3}-?[A-Z]{2}$', matricula):
        return "fr"
    elif re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', matricula):
        return "it"
    elif re.match(r'^[A-Z]{2}-?\d{2}-?[A-Z]{2}$', matricula):
        return "pt"
    else:
        return "unknown"

def extraer_matricula_valida(texto):
    texto = re.sub(r'[^A-Z0-9]', '', texto.upper())

    patrones = [
        r'\d{4}[BCDFGHJKLMNPRSTVWXYZ]{3}',  # ES
        r'[A-Z]{2}\d{2}[A-Z]{3}',          # UK
        r'[A-Z]{2}\d{3}[A-Z]{2}',          # IT
        r'[A-Z]{2}\d{2}[A-Z]{2}',          # PT
        r'[A-Z]{2}\d{3}[A-Z]{2}',          # FR simplificado
    ]

    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return match.group()

    return None

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

def gestionar_parking(matricula, accion):
    estado = get_estado(matricula)

    if estado == "dentro" and accion == "entrar":
        return "Ya estás dentro", False
    elif estado == "dentro" and accion == "salir":
        actualizar_estado(matricula, "fuera")
        return "Salida permitida", True
    elif estado == "fuera" and accion == "entrar":
        actualizar_estado(matricula, "dentro")
        return "Entrada permitida", True
    else:
        return "No puedes salir si no has entrado", False