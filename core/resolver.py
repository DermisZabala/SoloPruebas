# Archivo: core/resolver.py (VERSIÓN OPTIMIZADA PARA TIMEOUTS EN VERCEL)

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

if 'VERCEL' not in os.environ:
    from webdriver_manager.chrome import ChromeDriverManager

def get_m3u8_link(iframe_url: str, is_filemoon: bool = False) -> str | None:
    print(f"\n--- [SELENIUM-RESOLVER] Iniciando para: {iframe_url}")
    
    # Opciones de Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280x720") # Tamaño más pequeño
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    
    logging_prefs = {'performance': 'ALL'}
    chrome_options.set_capability('goog:loggingPrefs', logging_prefs)
    
    driver = None
    m3u8_url = None
    
    try:
        # --- Lógica de Entorno: Vercel vs. Local ---
        if 'VERCEL' in os.environ:
            print("[SELENIUM-RESOLVER] Entorno Vercel detectado.")
            chrome_options.binary_location = "/var/task/node_modules/chrome-aws-lambda/bin/chromium"
            service = ChromeService(executable_path="/var/task/node_modules/chrome-aws-lambda/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            print("[SELENIUM-RESOLVER] Entorno Local detectado.")
            driver_manager = ChromeDriverManager().install()
            service = ChromeService(executable_path=driver_manager)
            driver = webdriver.Chrome(service=service, options=chrome_options)

        print("[SELENIUM-RESOLVER] Driver de Chrome iniciado con éxito.")
        
        # === AJUSTE CLAVE DE TIMEOUT ===
        # Aumentamos el timeout de carga de la página. Si no carga en 20s, falla.
        driver.set_page_load_timeout(20) 
        
        print(f"[SELENIUM-RESOLVER] Navegando a {iframe_url} (timeout de 20s)...")
        driver.get(iframe_url)
        
        # Reducimos la espera estática, confiamos más en las esperas explícitas.
        time.sleep(2) 
        
        try:
            if is_filemoon:
                # Damos más tiempo para encontrar el iframe en Filemoon
                wait = WebDriverWait(driver, 20) 
                player_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='bkg']")))
                if player_iframe:
                    iframe_src = player_iframe.get_attribute('src')
                    driver.get(iframe_src)
                    time.sleep(3)
            
            # Aumentamos la espera para el botón de play
            wait = WebDriverWait(driver, 20)
            play_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jw-video.jw-reset, .vjs-big-play-button, video")))
            if play_button:
                driver.execute_script("arguments[0].click();", play_button)
                time.sleep(3) # Espera post-clic
        except Exception as e:
            print(f"[SELENIUM-RESOLVER] ADVERTENCIA: No se pudo hacer clic o encontrar iframe, continuando... ({e})")
        
        # Damos una última oportunidad de que las peticiones se registren
        time.sleep(2) 
        
        logs = driver.get_log('performance')
        found_urls = [log.get('params', {}).get('request', {}).get('url', '') for entry in logs for log in [json.loads(entry['message'])['message']] if 'Network.requestWillBeSent' in log.get('method', '') and '.m3u8' in log.get('params', {}).get('request', {}).get('url', '')]
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

# ... (El resto del archivo se queda igual) ...
def get_m3u8_from_streamwish(source_id):
    return get_m3u8_link(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    return get_m3u8_link(f"https://filemoon.sx/e/{source_id}", is_filemoon=True)
    
def get_m3u8_from_vidhide(source_id):
    return get_m3u8_link(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return get_m3u8_link(f"https://voe.sx/e/{source_id}")