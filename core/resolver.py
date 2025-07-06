# Archivo: core/resolver.py (VERSIÓN FINAL HÍBRIDA)

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def get_m3u8_link(iframe_url: str, is_filemoon: bool = False) -> str | None:
    """
    Función ÚNICA y robusta que usa Selenium.
    Tiene un modo especial para Filemoon que navega iframes.
    """
    print(f"\n--- [SELENIUM-RESOLVER] Iniciando para: {iframe_url}")
    
    # Configuración de Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = None
    m3u8_url = None
    
    try:
        # Inicializa el driver
        driver_manager = ChromeDriverManager().install()
        service = ChromeService(executable_path=driver_manager)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Carga la página y espera
        driver.get(iframe_url)
        print("[SELENIUM-RESOLVER] Página cargada, esperando 5s...")
        time.sleep(5)

        try:
            # === LÓGICA ESPECIAL PARA FILEMOON ===
            if is_filemoon:
                print("[SELENIUM-RESOLVER] MODO FILEMOON: Buscando iframe secundario...")
                wait = WebDriverWait(driver, 10)
                # Buscamos el iframe cuya URL contiene 'bkg'
                player_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='bkg']")))
                if player_iframe:
                    iframe_src = player_iframe.get_attribute('src')
                    print(f"[SELENIUM-RESOLVER] Iframe encontrado. Navegando a: {iframe_src}")
                    # En lugar de cambiar de contexto, navegamos directamente a la URL del iframe.
                    # Esto es más robusto contra las protecciones.
                    driver.get(iframe_src)
                    print("[SELENIUM-RESOLVER] Navegación a iframe completada. Esperando 5s...")
                    time.sleep(5)
                else:
                    print("[SELENIUM-RESOLVER] ADVERTENCIA: No se encontró el iframe secundario de Filemoon.")

            # --- LÓGICA DE CLIC (común para todos ahora) ---
            wait = WebDriverWait(driver, 15)
            # Buscamos el botón de play de JWPlayer, que es lo que usan
            play_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jw-video.jw-reset, .vjs-big-play-button, video")))
            
            if play_button:
                print("[SELENIUM-RESOLVER] Elemento de play encontrado. Forzando clic con JavaScript...")
                driver.execute_script("arguments[0].click();", play_button)
                print("[SELENIUM-RESOLVER] Clic ejecutado. Esperando 5s...")
                time.sleep(5)
            else:
                 print("[SELENIUM-RESOLVER] ADVERTENCIA: No se encontró elemento para hacer clic.")

        except Exception as e:
            print(f"[SELENIUM-RESOLVER] ADVERTENCIA durante el proceso de clic/iframe: {e}")
        
        # Busca el M3U8 en los logs de red
        print("[SELENIUM-RESOLVER] Analizando logs de red...")
        logs = driver.get_log('performance')
        found_urls = [
            log.get('params', {}).get('request', {}).get('url', '')
            for entry in logs
            for log in [json.loads(entry['message'])['message']]
            if 'Network.requestWillBeSent' in log.get('method', '') and '.m3u8' in log.get('params', {}).get('request', {}).get('url', '')
        ]

        if found_urls:
            master_m3u8 = next((url for url in found_urls if 'seg' not in url.lower() and 'chunk' not in url.lower()), None)
            m3u8_url = master_m3u8 if master_m3u8 else found_urls[-1]
            print(f"--- [SELENIUM-RESOLVER] ¡ÉXITO! M3U8 encontrado: {m3u8_url[:100]}...")
        else:
            print("--- [SELENIUM-RESOLVER] FALLO: No se encontró URL .m3u8.")

    except Exception as e:
        print(f"--- [SELENIUM-RESOLVER] ERROR CRÍTICO: {type(e).__name__}: {e}")
    finally:
        if driver:
            driver.quit()
    
    return m3u8_url

# --- FUNCIONES DE ENTRADA ---
def get_m3u8_from_streamwish(source_id):
    return get_m3u8_link(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    # Usamos la función principal de Selenium pero activamos el modo especial
    return get_m3u8_link(f"https://filemoon.sx/e/{source_id}", is_filemoon=True)
    
def get_m3u8_from_vidhide(source_id):
    return get_m3u8_link(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return get_m3u8_link(f"https://voe.sx/e/{source_id}")