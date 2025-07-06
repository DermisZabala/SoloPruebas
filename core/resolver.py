# Archivo: core/resolver.py (Tu código adaptado para Vercel)

import os
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

# Importamos webdriver_manager solo si NO estamos en Vercel
if 'VERCEL' not in os.environ:
    from webdriver_manager.chrome import ChromeDriverManager

def get_m3u8_link(iframe_url: str, is_filemoon: bool = False) -> str | None:
    print(f"\n--- [SELENIUM-RESOLVER] Iniciando para: {iframe_url}")
    
    # Configuración de Chrome (común para ambos entornos)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu") # Importante para entornos sin GPU
    chrome_options.add_argument("--window-size=1280x1696") # Tamaño estándar para headless
    
    # Habilitar logging de performance
    logging_prefs = {'performance': 'ALL'}
    chrome_options.set_capability('goog:loggingPrefs', logging_prefs)
    
    driver = None
    m3u8_url = None
    
    try:
        # --- LÓGICA DE INICIALIZACIÓN DEL DRIVER (LA PARTE CLAVE) ---
        if 'VERCEL' in os.environ:
            # ENTORNO VERCEL: Usa rutas fijas y no webdriver-manager
            print("[SELENIUM-RESOLVER] Entorno Vercel detectado. Usando rutas de chrome-aws-lambda.")
            chrome_options.binary_location = "/var/task/node_modules/chrome-aws-lambda/bin/chromium"
            service = ChromeService(executable_path="/var/task/node_modules/chrome-aws-lambda/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # ENTORNO LOCAL: Usa tu código original con webdriver-manager
            print("[SELENIUM-RESOLVER] Entorno Local detectado. Usando webdriver-manager.")
            driver_manager = ChromeDriverManager().install()
            service = ChromeService(executable_path=driver_manager)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("[SELENIUM-RESOLVER] Driver de Chrome iniciado con éxito.")
        
        # --- EL RESTO DE TU CÓDIGO FUNCIONAL SE MANTIENE INTACTO ---
        driver.get(iframe_url)
        print("[SELENIUM-RESOLVER] Página cargada, esperando 5s...")
        time.sleep(5)

        try:
            if is_filemoon:
                print("[SELENIUM-RESOLVER] MODO FILEMOON: Buscando iframe secundario...")
                wait = WebDriverWait(driver, 10)
                player_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='bkg']")))
                if player_iframe:
                    iframe_src = player_iframe.get_attribute('src')
                    driver.get(iframe_src)
                    time.sleep(5)
            
            wait = WebDriverWait(driver, 15)
            play_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jw-video.jw-reset, .vjs-big-play-button, video")))
            if play_button:
                driver.execute_script("arguments[0].click();", play_button)
                time.sleep(5)
        except Exception as e:
            print(f"[SELENIUM-RESOLVER] ADVERTENCIA durante el proceso de clic/iframe: {e}")
        
        print("[SELENIUM-RESOLVER] Analizando logs de red...")
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

# --- Las funciones de entrada no cambian ---
def get_m3u8_from_streamwish(source_id):
    return get_m3u8_link(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    return get_m3u8_link(f"https://filemoon.sx/e/{source_id}", is_filemoon=True)
    
def get_m3u8_from_vidhide(source_id):
    return get_m3u8_link(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return get_m3u8_link(f"https://voe.sx/e/{source_id}")