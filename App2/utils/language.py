import os
import re
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# Cargar .env
load_dotenv("credentials.env")
endpoint_PLN = os.getenv("PLN_ENDPOINT")
key_PLN = os.getenv("PLN_KEY")

MAX_CHARS = 4000  # Límite por solicitud de Azure

def get_client():
    return TextAnalyticsClient(
        endpoint=endpoint_PLN,
        credential=AzureKeyCredential(key_PLN)
    )

def limpiar_texto(texto: str) -> str:
    """Quita HTML, saltos de línea y espacios extra"""
    texto = re.sub(r'<.*?>', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def resumir_texto(texto: str) -> str:
    """Resumen robusto usando Azure Abstract Summary"""
    texto = limpiar_texto(texto)
    if not texto:
        return "⚠️ No hay texto para resumir."

    client = get_client()
    resumen_final = ""

    bloques = [texto[i:i+MAX_CHARS] for i in range(0, len(texto), MAX_CHARS)]

    for i, bloque in enumerate(bloques):
        try:
            poller = client.begin_abstract_summary([bloque], language="es")
            result = poller.result()  # ItemPaged

            for doc in result:
                if doc.is_error:
                    resumen_final += f"\n⚠️ Error en bloque {i+1}: {doc.error.message}\n"
                else:
                    for summary in doc.summaries:
                        resumen_final += summary.text + " "
        except Exception as e:
            resumen_final += f"\n⚠️ Error en bloque {i+1}: {e}\n"

    return resumen_final.strip()

def extraer_claves(texto: str) -> list:
    """Extrae ideas clave bloque por bloque"""
    texto = limpiar_texto(texto)
    if not texto:
        return ["⚠️ No hay texto para extraer claves."]

    client = get_client()
    claves_final = []

    bloques = [texto[i:i+MAX_CHARS] for i in range(0, len(texto), MAX_CHARS)]

    for i, bloque in enumerate(bloques):
        try:
            response = client.extract_key_phrases([bloque])[0]
            if response.is_error:
                claves_final.append(f"⚠️ Error en bloque {i+1}: {response.error.message}")
            else:
                claves_final.extend(response.key_phrases)
        except Exception as e:
            claves_final.append(f"⚠️ Error en bloque {i+1}: {e}")

    return list(dict.fromkeys(claves_final))