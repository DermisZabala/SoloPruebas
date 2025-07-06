# Archivo: core/resolver.py (VERSIÓN FINAL CON SCRAPERAPI)

import os
import re
import requests

def resolve_with_scraperapi(iframe_url: str) -> str | None:
    print(f"--- [SCRAPERAPI] Resolviendo: {iframe_url}")
    api_key = os.environ.get('SCRAPERAPI_KEY')
    if not api_key:
        print("--- [SCRAPERAPI] ERROR: Falta la variable de entorno SCRAPERAPI_KEY.")
        return None
    
    payload = {'api_key': api_key, 'url': iframe_url, 'render': 'true'}
    try:
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        response.raise_for_status()
        
        # Buscamos el M3U8 en el HTML que nos devuelve la API
        # Este patrón busca URLs que terminen en .m3u8 dentro de comillas
        m3u8_match = re.search(r'file:"(https?:\/\/[^"]+\.m3u8[^"]*)"', response.text)
        if m3u8_match:
            m3u8_url = m3u8_match.group(1)
            print(f"--- [SCRAPERAPI] ¡ÉXITO! M3U8 encontrado: {m3u8_url[:100]}...")
            return m3u8_url
        else:
            print("--- [SCRAPERAPI] FALLO: No se encontró la URL .m3u8 en la respuesta.")
            return None
    except requests.RequestException as e:
        print(f"--- [SCRAPERAPI] ERROR en la petición a la API: {e}")
        return None

def get_m3u8_from_streamwish(source_id):
    return resolve_with_scraperapi(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    # La lógica para Filemoon es especial porque tiene un iframe anidado
    try:
        main_page_url = f"https://filemoon.sx/e/{source_id}"
        api_key = os.environ.get('SCRAPERAPI_KEY')
        if not api_key: return None

        payload = {'api_key': api_key, 'url': main_page_url}
        response = requests.get('http://api.scraperapi.com', params=payload)
        iframe_match = re.search(r'<iframe src="([^"]+)"', response.text)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            # Ahora hacemos scraping a la URL del iframe con renderizado
            return resolve_with_scraperapi(iframe_url)
    except Exception as e:
        print(f"--- [FILEMOON-IFRAME] Error: {e}")
    return None
    
def get_m3u8_from_vidhide(source_id):
    return resolve_with_scraperapi(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return resolve_with_scraperapi(f"https://voe.sx/e/{source_id}")