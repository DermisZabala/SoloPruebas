# Archivo: core/resolver.py (VERSIÓN CON PARÁMETROS AVANZADOS PARA SCRAPERAPI)

import os
import re
import requests

def resolve_with_scraperapi(iframe_url: str, is_filemoon: bool = False) -> str | None:
    """
    Usa ScraperAPI con parámetros avanzados para aumentar la tasa de éxito.
    """
    print(f"--- [SCRAPERAPI] Resolviendo: {iframe_url}")
    api_key = os.environ.get('SCRAPERAPI_KEY')
    if not api_key:
        print("--- [SCRAPERAPI] ERROR: La variable de entorno SCRAPERAPI_KEY no está definida.")
        return None
    
    # --- PARÁMETROS AVANZADOS ---
    payload = {
        'api_key': api_key,
        'url': iframe_url,
        'render': 'true',         # Le pedimos que ejecute el JavaScript de la página
        'country_code': 'us'      # Forzamos que la petición venga desde una IP de EEUU (muy común, menos sospechoso)
    }
    
    try:
        # Aumentamos el timeout a 90 segundos para darle tiempo de sobra a páginas lentas
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=90)
        
        print(f"--- [SCRAPERAPI] Respuesta recibida de la API con estado: {response.status_code}")
        response.raise_for_status()
        
        # Usamos una expresión regular más robusta para encontrar la URL del M3U8
        m3u8_match = re.search(r'(https?:\/\/[^"\']+\.m3u8[^"\']*)', response.text)
        
        if m3u8_match:
            m3u8_url = m3u8_match.group(1).replace('&', '&') # Limpiamos la URL
            print(f"--- [SCRAPERAPI] ¡ÉXITO! M3U8 encontrado: {m3u8_url[:100]}...")
            return m3u8_url
        else:
            print("--- [SCRAPERAPI] FALLO: No se encontró la URL .m3u8 en la respuesta.")
            print("--- [SCRAPERAPI] Inicio de la respuesta HTML para depuración:")
            print(response.text[:2000]) # Imprime los primeros 2000 caracteres
            print("--- [SCRAPERAPI] Fin de la respuesta HTML.")
            return None
            
    except requests.RequestException as e:
        print(f"--- [SCRAPERAPI] ERROR en la petición a la API: {e}")
        return None

# --- LAS FUNCIONES DE ENTRADA NO CAMBIAN, EXCEPTO FILEMOON ---

def get_m3u8_from_streamwish(source_id):
    return resolve_with_scraperapi(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    # Filemoon necesita un tratamiento especial para el iframe
    try:
        main_page_url = f"https://filemoon.sx/e/{source_id}"
        api_key = os.environ.get('SCRAPERAPI_KEY')
        if not api_key: return None

        # Paso 1: Obtener la página principal SIN renderizar JS (más rápido)
        payload_no_render = {'api_key': api_key, 'url': main_page_url}
        response = requests.get('http://api.scraperapi.com', params=payload_no_render)
        
        iframe_match = re.search(r'<iframe src="([^"]+)"', response.text)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            # Paso 2: Ahora sí, hacemos scraping a la URL del iframe CON renderizado
            return resolve_with_scraperapi(iframe_url)
        else:
            print("--- [FILEMOON-IFRAME] No se pudo encontrar el iframe en la página principal.")
    except Exception as e:
        print(f"--- [FILEMOON-IFRAME] Error: {e}")
    return None
    
def get_m3u8_from_vidhide(source_id):
    return resolve_with_scraperapi(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return resolve_with_scraperapi(f"https://voe.sx/e/{source_id}")