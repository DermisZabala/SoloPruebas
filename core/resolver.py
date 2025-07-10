# Archivo: core/resolver.py (NUEVA VERSIÓN con Cloudscraper)

import re
import cloudscraper

# Creamos una única instancia de scraper para reutilizarla
# Esto mejora el rendimiento y la gestión de cookies/sesiones
scraper = cloudscraper.create_scraper()

def resolve_with_cloudscraper(iframe_url: str) -> str | None:
    """
    Usa la librería Cloudscraper para obtener el contenido de una URL
    y extraer el enlace .m3u8.
    """
    print(f"--- [Cloudscraper] Resolviendo: {iframe_url}")
    
    try:
        # Hacemos la petición directa a la URL del iframe
        response = scraper.get(iframe_url, timeout=20)
        
        print(f"--- [Cloudscraper] Respuesta recibida con estado: {response.status_code}")
        response.raise_for_status() # Lanza un error para códigos 4xx/5xx
        
        # Usamos la misma expresión regular robusta para encontrar el M3U8
        m3u8_match = re.search(r'(https?:\/\/[^"\']+\.m3u8[^"\']*)', response.text)
        
        if m3u8_match:
            m3u8_url = m3u8_match.group(1)
            print(f"--- [Cloudscraper] ¡ÉXITO! M3U8 encontrado: {m3u8_url[:100]}...")
            return m3u8_url
        else:
            print("--- [Cloudscraper] FALLO: No se encontró la URL .m3u8 en la respuesta.")
            # Descomenta la siguiente línea si necesitas depurar el HTML en los logs de Vercel
            # print(response.text[:2000])
            return None
            
    except Exception as e:
        print(f"--- [Cloudscraper] ERROR en la petición: {e}")
        return None

# --- LAS FUNCIONES DE ENTRADA NO CAMBIAN SU NOMBRE, SOLO SU LÓGICA INTERNA ---

def get_m3u8_from_streamwish(source_id):
    # Streamwish es directo, solo llamamos al resolver genérico
    return resolve_with_cloudscraper(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    # Filemoon a veces tiene un iframe dentro de otro.
    # Esta lógica es más simple y a menudo suficiente.
    return resolve_with_cloudscraper(f"https://filemoon.sx/e/{source_id}")
    
def get_m3u8_from_vidhide(source_id):
    # Vidhide (anteriormente Filelions) a menudo usa URLs como /v/
    return resolve_with_cloudscraper(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return resolve_with_cloudscraper(f"https://voe.sx/e/{source_id}")