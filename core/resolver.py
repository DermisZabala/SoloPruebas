# Archivo: core/resolver.py (VERSIÓN FINAL CON CLOUDSCRAPER)

import re
import cloudscraper

# Creamos una única instancia de scraper para reutilizarla.
# Esto mejora el rendimiento y la gestión de cookies/sesiones.
# Usamos un navegador común para evitar bloqueos.
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

def resolve_with_cloudscraper(iframe_url: str) -> str | None:
    """
    Usa la librería Cloudscraper para obtener el contenido de una URL
    y extraer el enlace .m3u8, simulando ser un navegador real.
    """
    print(f"--- [Cloudscraper] Resolviendo: {iframe_url}")
    
    try:
        # Añadimos cabeceras realistas para minimizar la probabilidad de bloqueo.
        # El 'Referer' es a menudo crucial.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': iframe_url
        }
        
        # Hacemos la petición directa a la URL del iframe
        response = scraper.get(iframe_url, timeout=25, headers=headers)
        
        print(f"--- [Cloudscraper] Respuesta recibida con estado: {response.status_code}")
        response.raise_for_status() # Lanza un error para códigos 4xx/5xx
        
        # Usamos la misma expresión regular robusta para encontrar el M3U8
        # Esta expresión busca cualquier URL que termine en .m3u8 con posibles parámetros
        m3u8_match = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*?)', response.text)
        
        if m3u8_match:
            m3u8_url = m3u8_match.group(1).replace('\\', '') # Limpiamos barras invertidas
            print(f"--- [Cloudscraper] ¡ÉXITO! M3U8 encontrado: {m3u8_url[:100]}...")
            return m3u8_url
        else:
            print("--- [Cloudscraper] FALLO: No se encontró la URL .m3u8 en la respuesta.")
            # Para depurar en Vercel, puedes ir a los logs del despliegue y ver esta salida.
            # print(f"--- HTML recibido ---\n{response.text[:2000]}\n--- Fin HTML ---")
            return None
            
    except Exception as e:
        print(f"--- [Cloudscraper] ERROR en la petición: {type(e).__name__}: {e}")
        return None

# --- LAS FUNCIONES DE ENTRADA NO CAMBIAN SU NOMBRE, SOLO SU LÓGICA INTERNA ---

def get_m3u8_from_streamwish(source_id):
    # Streamwish es directo, solo llamamos al resolver genérico
    return resolve_with_cloudscraper(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    # Filemoon a menudo es directo también
    return resolve_with_cloudscraper(f"https://filemoon.sx/e/{source_id}")
    
def get_m3u8_from_vidhide(source_id):
    # Vidhide (anteriormente Filelions) a menudo usa URLs como /v/
    return resolve_with_cloudscraper(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return resolve_with_cloudscraper(f"https://voe.sx/e/{source_id}")