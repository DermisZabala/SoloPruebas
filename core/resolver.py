# Archivo: core/resolver.py (VERSIÓN OPTIMIZADA PARA ARRANQUE RÁPIDO)

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

# Importamos webdriver_manager solo si no estamos en Vercel
if 'VERCEL' not in os.environ:
    from webdriver_manager.chrome import ChromeDriverManager

def get_m3u8_link(iframe_url: str, is_filemoon: bool = False) -> str | None:
    print(f"\n--- [RESOLVER] Iniciando para: {iframe_url}")
    
    driver = None
    m3u8_url = None
    
    try:
        # --- Configuración de Opciones Ultra-ligera ---
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--single-process") # Reduce el uso de memoria
        chrome_options.add_argument("--no-zygote")      # Ayuda en contenedores
        
        # --- Lógica de Entorno ---
        if 'VERCEL' in os.environ:
            print("[RESOLVER] Entorno Vercel detectado. Usando chrome-aws-lambda.")
            chrome_options.binary_location = "/var/task/node_modules/chrome-aws-lambda/bin/chromium"
            service = ChromeService(executable_path="/var/task/node_modules/chrome-aws-lambda/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            print("[RESOLVER] Entorno Local detectado.")
            driver_manager = ChromeDriverManager().install()
            service = ChromeService(executable_path=driver_manager)
            driver = webdriver.Chrome(service=service, options=chrome_options)

        print("[RESOLVER] Driver iniciado. Tiempo de espera de la página: 30s")
        driver.set_page_load_timeout(30) # Le damos hasta 30s para cargar la página
        
        # --- Lógica de Scraping (más rápida) ---
        driver.get(iframe_url)
        
        # En lugar de sleeps fijos, usamos esperas explícitas que son más eficientes
        wait = WebDriverWait(driver, 15)
        
        if is_filemoon:
            print("[RESOLVER] Modo Filemoon. Buscando y cambiando a iframe...")
            player_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='bkg']")))
            driver.switch_to.frame(player_iframe)
            print("[RESOLVER] Contexto cambiado a iframe.")

        # Hacemos clic y esperamos a que el video empiece a cargar
        print("[RESOLVER] Buscando botón de play...")
        play_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jw-video.jw-reset, .vjs-big-play-button, video")))
        driver.execute_script("arguments[0].click();", play_button)
        print("[RESOLVER] Clic ejecutado. Esperando que el src del video contenga 'm3u8'...")
        
        # Espera Inteligente: esperamos a que el atributo 'src' del video contenga '.m3u8'
        video_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        WebDriverWait(driver, 10).until(lambda d: ".m3u8" in (d.find_element(By.TAG_NAME, "video").get_attribute("src") or ""))
        
        m3u8_url = video_element.get_attribute("src")
        
        if m3u8_url:
            print(f"--- [RESOLVER] ¡ÉXITO! M3U8 encontrado en el tag <video>: {m3u8_url[:100]}...")
        else:
            print("--- [RESOLVER] FALLO: No se encontró la URL en el tag <video> después del clic.")

    except Exception as e:
        print(f"--- [RESOLVER] ERROR CRÍTICO: {type(e).__name__}: {e}")
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