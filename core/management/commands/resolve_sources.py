# Archivo: core/management/commands/resolve_sources.py

import json
import time
from pathlib import Path
from django.core.management.base import BaseCommand
from core import resolver # Importa nuestro resolver.py que funciona en local

# Mapa de funciones de nuestro resolver
RESOLVER_MAP = {
    'filemoon': resolver.get_m3u8_from_filemoon,
    'streamwish': resolver.get_m3u8_from_streamwish,
    'sw': resolver.get_m3u8_from_streamwish,
    'vidhide': resolver.get_m3u8_from_vidhide,
    'voesx': resolver.get_m3u8_from_voesx
}

class Command(BaseCommand):
    help = 'Recorre los archivos de datos JSON y usa Selenium para pre-resolver y almacenar los enlaces .m3u8.'

    def handle(self, *args, **kwargs):
        # Asumimos que tus archivos están en C:/mi-json1, C:/mi-json2, etc.
        # Ajusta esta ruta si es diferente
        base_path = Path("C:/")
        file_paths = [base_path / f"mi-json{i}/data{i}.json" for i in range(1, 4)]
        
        for file_path in file_paths:
            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f"Archivo {file_path} no encontrado, saltando."))
                continue

            self.stdout.write(self.style.SUCCESS(f"=== Procesando archivo: {file_path} ==="))
            
            try:
                with open(file_path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    content_updated = False

                    # Bucle para procesar películas, series y animes
                    for content_type in ['movies', 'series', 'anime']:
                        for item in data.get(content_type, []):
                            sources_to_process = []
                            # Fuentes de películas
                            if item.get('sources'):
                                sources_to_process.extend(item['sources'])
                            # Fuentes de episodios de series/animes
                            if item.get('seasons'):
                                for season in item.get('seasons', []):
                                    for episode in season.get('episodes', []):
                                        if episode.get('sources'):
                                            sources_to_process.extend(episode['sources'])
                            
                            for source in sources_to_process:
                                server_name = source.get('server_name', '').lower()
                                # Solo procesamos si no tiene ya una URL resuelta
                                if server_name in RESOLVER_MAP and not source.get('resolved_url'):
                                    embed_url = source.get('embed_url', '')
                                    if not embed_url: continue
                                    
                                    try:
                                        source_id = embed_url.strip('/').split('/')[-1]
                                    except IndexError:
                                        continue

                                    self.stdout.write(f"  -> Resolviendo {server_name} para '{item['title']}'...")
                                    m3u8_url = RESOLVER_MAP[server_name](source_id)
                                    
                                    # Guardamos el resultado (sea una URL o None)
                                    source['resolved_url'] = m3u8_url
                                    content_updated = True

                                    if m3u8_url:
                                        self.stdout.write(self.style.SUCCESS(f"     ¡Éxito! URL guardada."))
                                    else:
                                        self.stdout.write(self.style.WARNING(f"     Fallo. No se guardó URL."))
                                    
                                    time.sleep(5) # Pausa para no saturar
                    
                    # Si hemos modificado algo, volvemos a escribir el archivo
                    if content_updated:
                        f.seek(0)
                        json.dump(data, f, indent=4, ensure_ascii=False)
                        f.truncate()
                        self.stdout.write(self.style.SUCCESS(f"Archivo {file_path} actualizado."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"No se pudo procesar {file_path}. Error: {e}"))