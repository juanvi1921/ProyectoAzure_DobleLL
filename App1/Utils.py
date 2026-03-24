from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# Inicializar clientes
load_dotenv("credentials.env")

endpoint_PLN = os.getenv("PLN_ENDPOINT")
key_PLN = os.getenv("PLN_KEY")

client_PLN = TextAnalyticsClient(
    endpoint=endpoint_PLN,
    credential=AzureKeyCredential(key_PLN)
)

endpoint_VI = os.getenv("VISION_ENDPOINT")
key_VI = os.getenv("VISION_KEY")

client_VI = ComputerVisionClient(
    endpoint=endpoint_VI, 
    credentials=CognitiveServicesCredentials(key_VI)
)


# Función de OCR utilizando Azure Computer Vision
def leer_texto_azure(imagen):
    import time

    # Llamada OCR
    read_response = client_VI.read_in_stream(imagen, raw=True)

    # Obtener operation_id
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Esperar resultado
    while True:
        result = client_VI.get_read_result(operation_id)
        if result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    # Extraer texto
    texto_detectado = ""

    if result.status == "succeeded":
        for page in result.analyze_result.read_results:
            for line in page.lines:
                texto_detectado += line.text + "\n"

    return texto_detectado

# Funciones de Lenguaje Natural utilizando Azure Text Analytics

def detectar_idioma(texto):
    documentos = [texto]

    response = client_PLN.detect_language(documents=documentos)

    idioma = response[0].primary_language.name
    return idioma

def analizar_sentimiento(texto):
    documentos = [texto]

    response = client_PLN.analyze_sentiment(documents=documentos)

    sentimiento = response[0].sentiment
    return sentimiento

def clasificar_y_guardar(imagen, texto, idioma, sentimiento):
    # Carpeta base
    base_path = "archivos_clasificados"

    # Crear ruta dinámica
    carpeta = f"{base_path}/{idioma}/{sentimiento}"

    os.makedirs(carpeta, exist_ok=True)

    # Guardar imagen
    ruta_imagen = os.path.join(carpeta, imagen.name)

    with open(ruta_imagen, "wb") as f:
        f.write(imagen.getbuffer())

    # Guardar texto
    ruta_texto = os.path.join(carpeta, imagen.name + ".txt")

    with open(ruta_texto, "w", encoding="utf-8") as f:
        f.write(texto)

    return ruta_imagen

# Función adicional para extraer entidades nombradas (SIN USAR POR AHORA)
def extraer_entidades(texto):
    response = client_PLN.recognize_entities([texto])
    entidades = [ent.text for ent in response[0].entities]
    return entidades