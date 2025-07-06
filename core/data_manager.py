# Archivo: core/data_manager.py (CORREGIDO)

import json
import requests
from functools import lru_cache
from django.conf import settings

# --- FUNCIONES DE CACHÉ INDIVIDUALES PARA CADA RAW ---

@lru_cache(maxsize=3)
def get_data_from_raw(raw_key):
    """
    Función genérica para obtener y parsear un JSON desde una URL de GitHub.
    """
    if raw_key not in settings.GITHUB_RAW_URLS:
        print(f"FATAL: La clave '{raw_key}' no se encuentra en GITHUB_RAW_URLS en settings.py.")
        return {"movies": [], "series": [], "anime": []}
        
    url = settings.GITHUB_RAW_URLS[raw_key]
    print(f"Fetching data from GitHub ({raw_key}): {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched data from {raw_key}.")
        data = response.json()
        if 'movies' not in data: data['movies'] = []
        if 'series' not in data: data['series'] = []
        if 'anime' not in data: data['anime'] = []
        return data
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"FATAL: Could not fetch or parse data from {url}. Error: {e}")
        return {"movies": [], "series": [], "anime": []}

# --- FUNCIONES DE LÓGICA QUE USAN LOS DATOS CACHADOS ---

def get_all_movies():
    """Obtiene y combina TODAS las películas de los 3 archivos."""
    all_movies = []
    for raw_key in settings.GITHUB_RAW_URLS.keys():
        data = get_data_from_raw(raw_key)
        all_movies.extend(data.get('movies', []))
    return all_movies

def get_all_series():
    """Obtiene y combina TODAS las series de los 3 archivos."""
    all_series = []
    for raw_key in settings.GITHUB_RAW_URLS.keys():
        data = get_data_from_raw(raw_key)
        all_series.extend(data.get('series', []))
    return all_series

def get_all_animes():
    """Obtiene y combina TODOS los animes de los 3 archivos."""
    all_animes = []
    for raw_key in settings.GITHUB_RAW_URLS.keys():
        data = get_data_from_raw(raw_key)
        all_animes.extend(data.get('anime', []))
    return all_animes

def get_all_content():
    """Devuelve todo el contenido, combinando películas, series y animes."""
    all_content = get_all_movies() + get_all_series() + get_all_animes()
    # La ordenación se mueve a get_paginated_content para manejar los None correctamente
    return all_content

def find_movie_by_id(movie_id):
    """Encuentra una película por su ID."""
    for movie in get_all_movies():
        if movie.get('id') == movie_id:
            return movie
    return None

def find_series_by_id(content_id):
    """Encuentra una serie O ANIME por su ID."""
    all_series_and_animes = get_all_series() + get_all_animes()
    for item in all_series_and_animes:
        if item.get('id') == content_id:
            return item
    return None

def get_paginated_content(content_type='all', page=1, per_page=30):
    """Devuelve contenido paginado. Lógica corregida para ordenar después de filtrar."""
    
    # 1. Selecciona la lista correcta ANTES de ordenar
    if content_type == 'movies':
        content_list = get_all_movies()
    elif content_type == 'series':
        content_list = get_all_series()
    elif content_type == 'anime':
        content_list = get_all_animes()
    else: # 'all'
        content_list = get_all_content()

    # 2. Ordena la lista específica, manejando fechas que puedan ser None
    # --- LÍNEA CORREGIDA ---
    sorted_content = sorted(content_list, key=lambda x: x.get('release_date') or '1900-01-01', reverse=True)

    # 3. La lógica de paginación no cambia
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_items = sorted_content[start:end]
    has_more = len(sorted_content) > end
    
    return paginated_items, has_more