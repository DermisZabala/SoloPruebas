# Archivo: core/resolver.py (VERSIÓN CON DEPURADORES PARA VERCEL)

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Importamos webdriver_manager solo si no estamos en Vercel
if 'VERCEL' not in os.environ:
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService

def get_m3u8_link(iframe_url: str, is_filemoon: bool = False) -> str | None:
    print(f"\n--- [RESOLVER] Iniciando para: {iframe_url}")
    
    # Configuración de Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = None
    m3u8_url = None
    
    try:
        # --- Lógica de Entorno: Vercel (Bright Data) vs. Local (WebDriverManager) ---
        if 'VERCEL' in os.environ:
            print("[RESOLVER-VERCEL] 1. Entorno Vercel detectado. Intentando conectar a Bright Data...")
            
            user = os.environ.get('BRIGHTDATA_USERNAME')
            password = os.environ.get('BRIGHTDATA_PASSWORD')
            host = os.environ.get('BRIGHTDATA_HOST')
            port = os.environ.get('BRIGHTDATA_PORT')
            
            if not all([user, password, host, port]):
                print("[RESOLVER-VERCEL] ERROR FATAL: Faltan una o más variables de entorno de Bright Data.")
                return None
            
            print(f"[RESOLVER-VERCEL] 2. Credenciales encontradas. Usuario: {user}, Host: {host}")
            
            remote_url = f'http://{user}:{password}@{host}:{port}'
            print("[RESOLVER-VERCEL] 3. URL de conexión remota construida.")
            
            print("[RESOLVER-VERCEL] 4. Intentando instanciar webdriver.Remote...")
            driver = webdriver.Remote(command_executor=remote_url, options=chrome_options)
            print("[RESOLVER-VERCEL] 5. ¡ÉXITO! Conexión a webdriver.Remote establecida.")
        else:
            # ENTORNO DE DESARROLLO (TU PC LOCAL)
            print("[RESOLVER-LOCAL] Entorno Local detectado. Usando webdriver-manager.")
            driver_manager = ChromeDriverManager().install()
            service = ChromeService(executable_path=driver_manager)
            driver = webdriver.Chrome(service=service, options=chrome_options)

        print("[RESOLVER-COMÚN] 6. Driver conectado. Navegando a la página...")
        
        driver.get(iframe_url)
        print("[RESOLVER-COMÚN] 7. Página cargada. Esperando 5s...")
        time.sleep(5)
        
        try:
            print("[RESOLVER-COMÚN] 8. Iniciando bloque de clic...")
            if is_filemoon:
                print("[RESOLVER-COMÚN] 8.1. MODO FILEMOON: Buscando iframe secundario...")
                wait = WebDriverWait(driver, 15)
                player_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='bkg']")))
                if player_iframe:
                    iframe_src = player_iframe.get_attribute('src')
                    driver.get(iframe_src)
                    print("[RESOLVER-COMÚN] 8.2. Navegación a iframe completada. Esperando 5s...")
                    time.sleep(5)
            
            wait = WebDriverWait(driver, 15)
            play_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jw-video.jw-reset, .vjs-big-play-button, video")))
            if play_button:
                driver.execute_script("arguments[0].click();", play_button)
                print("[RESOLVER-COMÚN] 8.3. Clic forzado con éxito. Esperando 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"[RESOLVER-COMÚN] 8.ERROR. ADVERTENCIA durante el proceso de clic/iframe: {e}")
        
        print("[RESOLVER-COMÚN] 9. Buscando M3U8 en el atributo 'src' del tag de video...")
        
        video_tags = driver.find_elements(By.TAG_NAME, "video")
        print(f"[RESOLVER-COMÚN] 9.1. Se encontraron {len(video_tags)} tags de video.")
        for i, video in enumerate(video_tags):
            src = video.get_attribute('src')
            print(f"[RESOLVER-COMÚN] 9.2.{i}. Analizando video tag. SRC = {src[:100] if src else 'None'}")
            if src and '.m3u8' in src:
                m3u8_url = src
                print(f"--- [RESOLVER-COMÚN] 9.3. ¡ÉXITO! M3U8 encontrado.")
                break

        if not m3u8_url:
            print("--- [RESOLVER-COMÚN] 10. FALLO: No se encontró URL .m3u8 en los tags de video.")

    except Exception as e:
        print(f"--- [RESOLVER-COMÚN] ERROR CRÍTICO GENERAL: {type(e).__name__}: {e}")
    finally:
        if driver:
            print("[RESOLVER-COMÚN] 11. Cerrando el driver.")
            driver.quit()
    
    print(f"[RESOLVER] Finalizado. URL devuelta: {m3u8_url}")
    return m3u8_url

# --- Funciones de entrada (no cambian) ---
# ... (el resto del archivo se queda igual)
def get_m3u8_from_streamwish(source_id):
    return get_m3u8_link(f"https://streamwish.to/e/{source_id}")

def get_m3u8_from_filemoon(source_id):
    return get_m3u8_link(f"https://filemoon.sx/e/{source_id}", is_filemoon=True)
    
def get_m3u8_from_vidhide(source_id):
    return get_m3u8_link(f"https://filelions.to/v/{source_id}")

def get_m3u8_from_voesx(source_id):
    return get_m3u8_link(f"https://voe.sx/e/{source_id}")