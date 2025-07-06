# Archivo: core/management/commands/_utils.py (VERSIÓN FINAL CON NORMALIZACIÓN MEJORADA)

import json
import re
import time
import random
import unicodedata
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# --- Constantes y Headers ---
ANIMEFLV_BASE_URL = "https://www3.animeflv.net"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
ANILIST_API_URL = 'https://graphql.anilist.co'
# ... (las funciones get_data_file_path, load_local_data, save_local_data, update_data_list se mantienen igual)...
def get_data_file_path(index):
    if index not in [1, 2, 3]:
        raise ValueError("El índice del archivo debe ser 1, 2 o 3.")
    return Path(f"C:/mi-json{index}/data{index}.json")

def load_local_data(file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists() or file_path.stat().st_size == 0:
        return {"movies": [], "series": [], "anime": []}
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if 'movies' not in data: data['movies'] = []
            if 'series' not in data: data['series'] = []
            if 'anime' not in data: data['anime'] = []
            return data
        except json.JSONDecodeError:
            return {"movies": [], "series": [], "anime": []}

def save_local_data(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_data_list(data_list, new_item):
    found_idx = next((i for i, item in enumerate(data_list) if item.get('id') == new_item.get('id')), -1)
    if found_idx != -1:
        data_list[found_idx] = new_item
    else:
        data_list.append(new_item)

# ======================================================
# === LÓGICA DE ANILIST (VERSIÓN MEJORADA Y ROBUSTA)
# ======================================================

def _make_anilist_request(query, variables):
    """Función centralizada para hacer peticiones a AniList con reintentos."""
    for attempt in range(3): # Reintentar hasta 3 veces
        try:
            response = requests.post(ANILIST_API_URL, json={'query': query, 'variables': variables}, timeout=20)
            response.raise_for_status() # Lanza un error para códigos 4xx/5xx
            return response.json()
        except requests.RequestException as e:
            print(f"\n  [AniList] Advertencia: Falló la petición para ID {variables.get('id', '')}. {e}")
            if attempt < 2:
                wait_time = (attempt + 1) * 2
                print(f"  -> Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
    print(f"  [AniList] Fallaron todos los intentos para ID {variables.get('id', '')}. Se omite.")
    return None

def _explore_relations(start_id, all_parts_map, visited_ids):
    if start_id in visited_ids:
        return
    visited_ids.add(start_id)
    print(f"  [AniList] Explorando ID: {start_id}...", end='\r')

    query = '''query ($id: Int) { Media (id: $id, type: ANIME) { id, title { romaji }, format, startDate { year }, relations { edges { relationType(version: 2), node { id, format } } } } }'''
    response_data = _make_anilist_request(query, {'id': start_id})

    if not response_data:
        return

    media = response_data.get('data', {}).get('Media')
    if media and media.get('format'):
        if media['id'] not in all_parts_map:
            all_parts_map[media['id']] = {
                'id': media['id'],
                'title': media['title']['romaji'],
                'year': media.get('startDate', {}).get('year'),
                'format': media.get('format')
            }
        
        valid_relations = ['SEQUEL', 'PREQUEL', 'PARENT', 'OTHER', 'ALTERNATIVE']
        for edge in media.get('relations', {}).get('edges', []):
            node = edge.get('node')
            if edge.get('relationType') in valid_relations and node and node.get('format'):
                _explore_relations(node['id'], all_parts_map, visited_ids)

def get_all_related_tv_seasons(start_id):
    all_parts_map = {}
    visited_ids = set()
    print("[AniList] Iniciando rastreador de franquicia...")
    _explore_relations(start_id, all_parts_map, visited_ids)
    print("\n[AniList] Rastreo de franquicia completado.")
    
    if not all_parts_map:
        return []
        
    tv_seasons_only = [part for part in all_parts_map.values() if part.get('format') == 'TV']
    
    if not tv_seasons_only:
        return []
        
    tv_seasons_only.sort(key=lambda x: (x.get('year') if x.get('year') is not None else 9999, x.get('title', '')))
    return tv_seasons_only

def get_anime_details(anilist_id):
    main_query = '''query ($id: Int) { Media (id: $id, type: ANIME) { id, title { romaji }, description(asHtml: false), startDate { year }, coverImage { extraLarge }, bannerImage, genres, format } }'''
    response_data = _make_anilist_request(main_query, {'id': anilist_id})
    if response_data and response_data.get('data') and response_data['data'].get('Media'):
        data = response_data['data']['Media']
        return {
            'id': data['id'], 'title': data['title']['romaji'],
            'title_romaji': data['title'].get('romaji'), 'overview': re.sub('<br>', '\n', data.get('description', '') or ""),
            'year': data.get('startDate', {}).get('year'), 'poster_path': data.get('coverImage', {}).get('extraLarge'),
            'backdrop_path': data.get('bannerImage'), 'genres': data.get('genres', []), 'format': data.get('format')
        }
    return None

def build_base_anime_json(anime_details):
    return {"id": anime_details['id'], "imdb_id": None, "title": anime_details['title_romaji'], "overview": anime_details['overview'], "poster_path": anime_details['poster_path'], "backdrop_path": anime_details['backdrop_path'], "type": "Anime", "release_date": f"{anime_details['year']}-01-01" if anime_details.get('year') else None, "rating": "N/A", "genres": anime_details['genres'], "cast": [], "seasons": []}


# ======================================================
# === FUNCIONES DE SCRAPING (CON NORMALIZACIÓN MEJORADA)
# ======================================================

def normalize_text(text):
    """
    Normaliza el texto para comparación: minúsculas, sin tildes,
    reemplazos específicos y eliminación de caracteres no deseados.
    """
    if not text:
        return ""
    
    # 1. Reemplazos específicos ANTES de la normalización general.
    replacements = {
        '×': ' x ', # Hunter×Hunter -> Hunter x Hunter
        '·': ' ',   # Ej: "Code Geass: Hangyaku no Lelouch"
        ':': ' ',   # Reemplaza dos puntos por espacio
        '-': ' ',   # Reemplaza guiones por espacio
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # 2. Convertir a minúsculas
    text = text.lower()
    
    # 3. Normalizar para quitar tildes y otros diacríticos
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    
    # 4. Eliminar cualquier cosa que no sea letra, número o espacio
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # 5. Normalizar espacios (múltiples espacios a uno solo y quitar los de los extremos)
    return " ".join(text.split())

def search_on_animeflv(title_to_try):
    # ...
    # (El resto del archivo no cambia)
    try:
        response = requests.get(f"{ANIMEFLV_BASE_URL}/browse", params={'q': title_to_try}, timeout=15, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        for item in soup.select('div.Container ul.ListAnimes > li'):
            a_tag = item.select_one('a'); title_tag = a_tag.select_one('h3.Title'); year_tag = a_tag.select_one('p span.Date')
            if a_tag: results.append({'url': ANIMEFLV_BASE_URL + a_tag['href'], 'title': title_tag.text.strip() if title_tag else "", 'year': year_tag.text.strip() if year_tag else ""})
        return results
    except requests.RequestException: return []

def find_best_match_animeflv(season_data, search_results):
    if not search_results: return None
    best_match, highest_score = None, -1
    
    # Usamos nuestra nueva y mejorada función de normalización
    normalized_base_title = normalize_text(season_data['title'])
    base_title_words = set(normalized_base_title.split())
    anilist_year = str(season_data.get('year', ''))
    anilist_format = season_data.get('format', '').upper()
    
    for res in search_results:
        # Normalizamos también el título del resultado de la misma manera
        normalized_res_title = normalize_text(res['title'])
        if not normalized_res_title: continue
        
        res_title_words = set(normalized_res_title.split())
        
        common_words = len(base_title_words.intersection(res_title_words))
        total_unique_words = len(base_title_words.union(res_title_words))
        jaccard_similarity = common_words / total_unique_words if total_unique_words > 0 else 0
        title_score = jaccard_similarity * 200
        
        year_score = 0
        if anilist_year:
            # Damos un bonus GIGANTE si el año coincide exactamente.
            if res.get('year') and res.get('year') == anilist_year:
                year_score = 150
            # Damos un bonus más pequeño si el año está cerca (útil para series largas)
            elif res.get('year'):
                try:
                    year_diff = abs(int(res.get('year')) - int(anilist_year))
                    if year_diff <= 1:
                        year_score = 75
                except (ValueError, TypeError):
                    pass
        
        format_score = 0
        res_title_lower = res['title'].lower()
        if anilist_format == 'TV':
            if '(tv)' in res_title_lower or 'season' in res_title_lower: format_score += 30
            if 'movie' in res_title_lower or 'pelicula' in res_title_lower or 'ova' in res_title_lower: format_score -= 50
        
        total_score = title_score + year_score + format_score
        
        if total_score > highest_score:
            highest_score, best_match = total_score, res
            
    if highest_score > 100: # Umbral de confianza
        return best_match
    return None

def scrape_episode_sources(episode_url):
    try:
        page_response = requests.get(episode_url, timeout=15, headers=HEADERS); page_response.raise_for_status()
        soup = BeautifulSoup(page_response.content, 'html.parser')
        script_content = next((s.string for s in soup.find_all("script") if s.string and "var videos = " in s.string), None)
        if script_content:
            match = re.search(r"var videos = (\{.*?\});", script_content)
            if match:
                videos_data = json.loads(match.group(1)); sources = []
                for video_source in videos_data.get('SUB', []):
                    server_name = video_source.get('title'); embed_url = video_source.get('code')
                    if server_name and embed_url: sources.append({'language': 'Subtitulado', 'server_name': server_name, 'embed_url': embed_url})
                return sources
        return []
    except Exception: return []

def scrape_animeflv_page_details(animeflv_url):
    details = {'synopsis': '', 'episodes_list': []}
    try:
        response = requests.get(animeflv_url, timeout=10, headers=HEADERS); response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        synopsis_tag = soup.select_one('div.Description > p')
        if synopsis_tag: details['synopsis'] = synopsis_tag.get_text(strip=True)
        script_content = next((s.string for s in soup.find_all("script") if s.string and "var episodes = " in s.string), None)
        if not script_content: return details
        match = re.search(r"var episodes = (\[\[.*?\]\]);", script_content); slug_match = re.search(r"/anime/([^/]+)", animeflv_url)
        if not match or not slug_match: return details
        episodes_data = json.loads(match.group(1)); anime_slug = slug_match.group(1)
        details['episodes_list'] = sorted([{'number': int(ep[0]), 'url': f"{ANIMEFLV_BASE_URL}/ver/{anime_slug}-{ep[0]}"} for ep in episodes_data], key=lambda x: x['number'])
        return details
    except Exception: return details

def find_animeflv_page_data(season_data):
    """
    Paso 1 (Ligero): Busca en AnimeFLV y encuentra la mejor coincidencia.
    Devuelve el diccionario del 'best_match' (url, title) o None. No scrapea episodios.
    """
    print(f"  -> Buscando coincidencia para '{season_data['title']}' en AnimeFLV...")
    search_results = search_on_animeflv(season_data['title'])
    if not search_results:
        print("    -> No se encontraron resultados de búsqueda.")
        return None

    best_match = find_best_match_animeflv(season_data, search_results)
    if not best_match:
        print("    -> No se encontró una coincidencia fiable.")
        return None
    
    print(f"    -> Coincidencia encontrada: '{best_match['title']}' (URL: {best_match['url']})")
    return best_match

def scrape_episodes_from_page(animeflv_url):
    """
    Paso 2 (Pesado): A partir de una URL, hace el scraping de la sinopsis y todos los episodios.
    Devuelve (synopsis, episodes_list_with_sources)
    """
    page_details = scrape_animeflv_page_details(animeflv_url)
    synopsis = page_details['synopsis']
    episodes_list = page_details['episodes_list']

    if not episodes_list:
        return synopsis, []

    all_episodes_with_sources = []
    total_episodes = len(episodes_list)
    print(f"  -> Scrapeando fuentes para {total_episodes} episodios...")
    for i, ep_info in enumerate(episodes_list):
        print(f"    -> Episodio {ep_info['number']} ({i + 1}/{total_episodes})...", end='\r')
        sources = scrape_episode_sources(ep_info['url'])
        if sources: all_episodes_with_sources.append({"episode_number": ep_info['number'], "title": f"Episodio {ep_info['number']}", "overview": "", "sources": sources})
        time.sleep(random.uniform(0.1, 0.2))
    
    print("\n    -> Scraping de episodios completado.")
    return synopsis, all_episodes_with_sources