import requests
from bs4 import BeautifulSoup

def hacer_scraping(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    titulares = []
    textos = []

    for noticia in soup.find_all("article"):
        titulo = noticia.find("h2") or noticia.find("h3")  # algunos usan h3
        if titulo:
            titulares.append(titulo.get_text())
        
        # Extraer todo el texto dentro del artículo
        cuerpo = " ".join([p.get_text() for p in noticia.find_all("p")])
        if cuerpo:
            textos.append(cuerpo)

    return titulares, " ".join(textos)