from utils.scraping import hacer_scraping

# Cambia la URL por la del periódico que quieres probar
url = "https://elpais.com/"

titulares, texto = hacer_scraping(url)

print("=== Titulares ===")
for t in titulares:
    print("-", t)



from utils.language import resumir_texto, extraer_claves

resumen = resumir_texto(texto)
print("\n=== Resumen ===")
print(resumen)