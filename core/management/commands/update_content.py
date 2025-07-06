# Archivo: core/management/commands/update_content.py (Versión Final Unificada)

import json
import time
import re
import random
import cloudscraper
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

# --- Funciones Principales ---

def find_correct_cuevana_slug(scraper, tmdb_id, title, is_movie):
    print("\n--- Buscando en Cuevana para encontrar el Slug real... ---")
    try:
        search_query = quote(title)
        search_url = f"https://www.cuevana.is/buscar?q={search_query}"
        response = scraper.get(search_url, timeout=30)
        
        if response.status_code != 200:
            print(f"  -> FALLO en búsqueda de Slug: Cuevana devolvió estado {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        content_type_path = 'pelicula' if is_movie else 'serie'
        
        for link in soup.select('ul.MovieList > li.TPostMv > a'):
            href = link.get('href', '')
            if f"/{content_type_path}/{tmdb_id}/" in href:
                match = re.search(f"/{content_type_path}/{tmdb_id}/(.*?)/?$", href)
                if match and match.group(1):
                    found_slug = match.group(1).strip('/')
                    print(f"  -> ÉXITO: Slug correcto encontrado: '{found_slug}'")
                    return found_slug
        print("  -> No se encontró una coincidencia fiable en la búsqueda de Cuevana.")
        return None
    except Exception as e:
        print(f"  -> FALLO durante la búsqueda de Slug. Tipo: {type(e).__name__} - {e}")
        return None

def scrape_from_cuevana(scraper, tmdb_id, slug, is_movie, season_num=None, ep_num=None):
    if is_movie:
        print(f"  -> Intentando Proveedor: Scraper (Cuevana)...")
    else:
        print(f"  -> Intentando Proveedor: Scraper (Cuevana) para S{season_num:02d}E{ep_num:02d}...")

    base_url = "https://www.cuevana.is"
    url_to_try = f"{base_url}/pelicula/{tmdb_id}/{slug}" if is_movie else f"{base_url}/serie/{tmdb_id}/{slug}/temporada/{season_num}/episodio/{ep_num}"
    print(f"     URL: {url_to_try}")

    for attempt in range(1): # 1 intento + 1 reintento
        try:
            main_page = scraper.get(url_to_try, timeout=25)
            
            if 500 <= main_page.status_code < 600:
                print(f"  -> FALLO TEMPORAL (Cuevana): Estado {main_page.status_code}. Reintentando...")
                time.sleep(5)
                continue

            if main_page.status_code != 200:
                print(f"  -> FALLO (Cuevana): Página devolvió estado {main_page.status_code}")
                return {'sources': [], 'has_spanish': False}

            soup = BeautifulSoup(main_page.content, 'html.parser')
            sources = []
            has_spanish_source = False
            for link_tab in soup.select('ul.sub-tab-lang > li.clili'):
                player_url = link_tab.get('data-tr')
                if not player_url: continue
                try:
                    lang_div = link_tab.find_previous('div', class_='_1R6bW_0').select_one('span')
                    lang = (lang_div.text.strip().split(' ')[0] if lang_div else 'Desconocido').replace('Castellano', 'Español')
                    if lang in ['Español', 'Latino']: has_spanish_source = True
                    player_page = scraper.get(player_url, timeout=15)
                    if player_page.status_code != 200: continue
                    match = re.search(r"var url = '(.*?)';", player_page.text)
                    if match:
                        final_url = match.group(1)
                        srv_tag = link_tab.select_one('span.cdtr > span')
                        server_name = "Desconocido"
                        if srv_tag and srv_tag.text.strip():
                            parts = srv_tag.text.strip().lower().split(' ')
                            if len(parts) > 1:
                                server_name = parts[1].split('.')[0].capitalize()
                        sources.append({"language": lang, "server_name": server_name, "embed_url": final_url})
                except Exception:
                    continue
            
            if sources:
                print(f"  -> ÉXITO (Cuevana): Extraídas {len(sources)} URLs. ¿Fuente en español/latino? {'Sí' if has_spanish_source else 'No'}")
            else:
                print("  -> FALLO (Cuevana): No se encontraron fuentes de video en la página.")
            return {'sources': sources, 'has_spanish': has_spanish_source}
        except Exception as e:
            print(f"  -> FALLO DE RED (Cuevana) - Intento {attempt + 1}. Tipo: {type(e).__name__}")
            if attempt == 0: time.sleep(5)

    return {'sources': [], 'has_spanish': False}

def scrape_from_vidsrc(tmdb_id, is_movie, season_num=None, ep_num=None):
    if not is_movie:
        print(f"  -> Intentando Proveedor: API (vidsrc.to) para S{season_num:02d}E{ep_num:02d}...")
    
    content_type = 'movie' if is_movie else 'tv'
    embed_url = f"https://vidsrc.to/embed/{content_type}/{tmdb_id}"
    if not is_movie:
        embed_url += f"/{season_num}/{ep_num}"

    print(f"  -> ÉXITO (API): Añadido enlace de Vidsrc.")
    return [{"language": "Subtitulado", "server_name": "Vidsrc", "embed_url": embed_url}]


class Command(BaseCommand):
    help = 'Añade o actualiza contenido en un archivo JSON específico.'

    def add_arguments(self, parser):
        parser.add_argument('--file-index', type=int, choices=[1, 2, 3], required=True, help='El índice del archivo JSON a usar.')
        parser.add_argument('tmdb_id', type=int, help='El ID de TMDB del contenido.')
        parser.add_argument('--type', type=str, choices=['movie', 'series'], required=True, help='Tipo de contenido.')
        parser.add_argument('--seasons', type=str, help='(Opcional, para series) "5" o "1-8".')
        
    # --- FUNCIÓN CLAVE CORREGIDA ---
    # Volvemos al método antiguo para guardar en una ruta fija en C:
    def get_data_file_path(self, index):
        if index not in [1, 2, 3]:
            raise CommandError("El índice del archivo debe ser 1, 2 o 3.")
        # Se asegura de que la ruta use barras inclinadas normales, que Path maneja bien.
        return Path(f"C:/mi-json{index}/data{index}.json")

    def load_local_data(self, file_path):
        # Esta función crea la carpeta si no existe (ej. C:\mi-json1)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists() or file_path.stat().st_size == 0:
            initial_data = {"movies": [], "series": []}
            self.save_local_data(initial_data, file_path)
            return initial_data
        with open(file_path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {"movies": [], "series": []}

    def save_local_data(self, data, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.stdout.write(self.style.SUCCESS(f"\nDatos guardados exitosamente en '{file_path}'"))

    def handle(self, *args, **kwargs):
        file_index = kwargs['file_index']
        tmdb_id = kwargs['tmdb_id']
        content_type = kwargs['type']
        
        scraper = cloudscraper.create_scraper()
        
        target_file = self.get_data_file_path(file_index)
        self.stdout.write(self.style.NOTICE(f"--- Usando archivo de destino: {target_file} ---"))
        local_data = self.load_local_data(target_file)
        
        # --- INICIO DE LA CORRECCIÓN ---
        # Aseguramos que las claves principales siempre existan después de cargar el JSON.
        # Si la clave no existe, la crea con una lista vacía. Si ya existe, no hace nada.
        local_data.setdefault('movies', [])
        local_data.setdefault('series', [])
        # --- FIN DE LA CORRECCIÓN ---
        
        TMDB_API_KEY = "6427de0dc39f16b5707362359d15337f" 
        api_content_type = 'tv' if content_type == 'series' else 'movie'
        api_url = f"https://api.themoviedb.org/3/{api_content_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=es-ES&append_to_response=external_ids,credits"
        response = scraper.get(api_url)
        if response.status_code != 200:
            raise CommandError(f'Fallo al obtener datos de TMDB (status {response.status_code}).')
        tmdb_data = response.json()
        
        title = tmdb_data.get('title') or tmdb_data.get('name')
        release_date = tmdb_data.get('release_date') or tmdb_data.get('first_air_date')
        is_movie = content_type == 'movie'
        
        slug = find_correct_cuevana_slug(scraper, tmdb_id, title, is_movie)
        if not slug:
            slug = slugify(title)
            self.stdout.write(self.style.WARNING(f"  -> AVISO: Usando slug por defecto generado: '{slug}'"))
            
        base_info = {
            "id": tmdb_data['id'], "imdb_id": tmdb_data.get('external_ids', {}).get('imdb_id'),
            "title": title, "overview": tmdb_data.get('overview', ''),
            "poster_path": tmdb_data.get('poster_path', ''), "backdrop_path": tmdb_data.get('backdrop_path', ''),
            "release_date": release_date, "rating": f"{tmdb_data.get('vote_average', 0):.1f}",
            "genres": [g['name'] for g in tmdb_data.get('genres', [])],
            "cast": [m['name'] for m in tmdb_data.get('credits', {}).get('cast', [])[:5]]
        }

        if content_type == 'movie':
            base_info['type'] = 'Película'
            self.stdout.write(self.style.SUCCESS(f"\nProcesando película: {title}"))
            cuevana_result = scrape_from_cuevana(scraper, tmdb_id, slug, is_movie=True)
            if not cuevana_result['has_spanish']:
                self.stdout.write(self.style.ERROR(f"CANCELADO: La película '{title}' no tiene fuentes en Español/Latino. No se añadirá."))
                return
            vidsrc_sources = scrape_from_vidsrc(tmdb_id, is_movie=True)
            all_sources = cuevana_result['sources'] + vidsrc_sources
            base_info['sources'] = self.clean_and_sort_sources(all_sources)
            # Ahora esto es seguro, porque 'movies' está garantizado
            self.update_data_list(local_data['movies'], base_info) 
        
        elif content_type == 'series':
            base_info['type'] = 'Serie'
            self.stdout.write(self.style.SUCCESS(f"\nProcesando serie: {title}"))
            series_json = self.process_series(scraper, base_info, tmdb_data, kwargs, TMDB_API_KEY, slug)
            if not series_json:
                self.stdout.write(self.style.ERROR(f"CANCELADO: La serie '{title}' no cumplió el requisito de tener al menos un episodio en Español/Latino. No se añadirá."))
                return
            # Y esto también es seguro, porque 'series' está garantizado
            self.update_data_list(local_data['series'], series_json)

        self.save_local_data(local_data, target_file)

    def process_series(self, scraper, base_info, tmdb_data, kwargs, api_key, slug):
        target_seasons = self.parse_seasons_range(kwargs.get('seasons'), tmdb_data)
        all_processed_seasons = []
        series_has_spanish_content = False # Bandera de calificación para toda la serie
        
        for season_num in target_seasons:
            season_data, season_had_spanish = self.process_season(scraper, season_num, base_info['id'], slug, api_key)
            if season_data and season_data.get('episodes'):
                all_processed_seasons.append(season_data)
                if season_had_spanish:
                    series_has_spanish_content = True # Si una temporada lo cumple, la serie entera es válida
        
        if not series_has_spanish_content:
            return None
        
        final_series_json = base_info.copy()
        final_series_json['seasons'] = sorted(all_processed_seasons, key=lambda s: s.get('season_number', 0))
        return final_series_json
        
    def process_season(self, scraper, season_num, tmdb_id, slug, api_key):
        self.stdout.write(f"\n--- Procesando Temporada {season_num} ---")
        season_detail_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_num}?api_key={api_key}&language=es-ES"
        season_response = scraper.get(season_detail_url)
        if season_response.status_code != 200:
            self.stdout.write(self.style.WARNING(f"No se pudieron obtener detalles para la Temporada {season_num}."))
            return None, False
            
        season_data = season_response.json()
        season_json = {"season_number": season_num, "episodes": []}
        season_had_spanish_episode = False # Bandera para esta temporada específica
        
        for ep_data in season_data.get('episodes', []):
            ep_num = ep_data['episode_number']
            ep_title = ep_data.get('name', f"Episodio {ep_num}")
            self.stdout.write(f"Buscando fuentes para S{season_num:02d}E{ep_num:02d}: {ep_title}")
            
            cuevana_result = scrape_from_cuevana(scraper, tmdb_id, slug, is_movie=False, season_num=season_num, ep_num=ep_num)
            if cuevana_result['has_spanish']:
                season_had_spanish_episode = True
            
            vidsrc_sources = scrape_from_vidsrc(tmdb_id, is_movie=False, season_num=season_num, ep_num=ep_num)
            all_sources = cuevana_result['sources'] + vidsrc_sources

            if all_sources:
                episode_json = {
                    "episode_number": ep_num, "title": ep_title,
                    "overview": ep_data.get('overview', ''),
                    "sources": self.clean_and_sort_sources(all_sources)
                }
                season_json['episodes'].append(episode_json)
            else:
                self.stdout.write(self.style.WARNING(f"  -> OMITIDO: Episodio S{season_num:02d}E{ep_num:02d} no tiene ninguna fuente."))
            
            time.sleep(random.uniform(0.3, 0.8))

        return season_json, season_had_spanish_episode

    def parse_seasons_range(self, seasons_str, tmdb_data):
        if not seasons_str:
            self.stdout.write(self.style.NOTICE("No se especificó --seasons. Se procesarán TODAS las temporadas."))
            return [s['season_number'] for s in tmdb_data.get('seasons', []) if s.get('season_number', 0) > 0]
        if '-' in seasons_str:
            try: start, end = map(int, seasons_str.split('-')); return list(range(start, end + 1))
            except ValueError: raise CommandError('Formato de rango inválido.')
        else:
            try: return [int(seasons_str)]
            except ValueError: raise CommandError('Formato de temporada inválido.')

    def clean_and_sort_sources(self, all_raw_sources):
        random.shuffle(all_raw_sources)
        final_sources, language_priority_order = [], ["Latino", "Español", "Subtitulado"]
        language_limits = {"Latino": 8, "Español": 8, "Subtitulado": 4}
        seen_servers_by_lang = {lang: set() for lang in language_priority_order}
        for lang in language_priority_order:
            lang_added_count = 0
            for source in all_raw_sources:
                if source.get('language') == lang:
                    if lang_added_count >= language_limits[lang]: break
                    server_name = source.get('server_name')
                    if server_name and server_name not in seen_servers_by_lang[lang]:
                        final_sources.append(source)
                        seen_servers_by_lang[lang].add(server_name)
                        lang_added_count += 1
        return final_sources

    def update_data_list(self, data_list, new_item):
        found_idx = next((i for i, item in enumerate(data_list) if item.get('id') == new_item.get('id')), -1)
        
        if found_idx != -1:
            self.stdout.write(self.style.SUCCESS(f"\nEntrada existente encontrada para '{new_item['title']}'. Actualizando..."))
            
            if new_item.get('type') == 'Serie':
                existing_item = data_list[found_idx]
                newly_processed_seasons = {s['season_number']: s for s in new_item.get('seasons', [])}
                seasons_to_keep = [s for s in existing_item.get('seasons', []) if s.get('season_number') not in newly_processed_seasons]
                final_seasons = seasons_to_keep + list(newly_processed_seasons.values())
                final_seasons.sort(key=lambda s: s.get('season_number', 0))
                
                base_info_to_update = {k: v for k, v in new_item.items() if k != 'seasons'}
                existing_item.update(base_info_to_update)
                existing_item['seasons'] = final_seasons
                data_list[found_idx] = existing_item
            else:
                data_list[found_idx] = new_item
        else:
            self.stdout.write(self.style.SUCCESS(f"\nNueva entrada añadida para '{new_item['title']}'."))
            data_list.append(new_item)