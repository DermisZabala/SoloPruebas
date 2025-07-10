# Archivo: core/views.py (VERSIÓN CORREGIDA Y REORGANIZADA)

# -----------------------------------------------------------------
# 1. IMPORTS
# -----------------------------------------------------------------
# Imports de Django
from django.shortcuts import render, reverse
from django.http import Http404, JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

# Imports de librerías estándar
import unicodedata
import re
import requests
import base64
from urllib.parse import urljoin

# Imports locales del proyecto
from . import data_manager
from . import resolver

# -----------------------------------------------------------------
# 2. FUNCIONES DE AYUDA (HELPERS)
# -----------------------------------------------------------------
def get_sorted_sources(sources_dict):
    """
    Toma el diccionario de fuentes y devuelve una lista de tuplas
    ordenada según una prioridad de idiomas predefinida.
    """
    language_priority = ["Latino", "Español", "Subtitulado"]
    sorted_list = []
    
    for lang in language_priority:
        if lang in sources_dict:
            sorted_list.append((lang, sources_dict[lang]))
            
    for lang, sources in sources_dict.items():
        if lang not in language_priority:
            sorted_list.append((lang, sources))
            
    return sorted_list

def sort_sources_by_preference(sources_dict):
    """
    Ordena las fuentes de video dentro de cada idioma según una lista de preferencia.
    """
    server_preference = ["MEGA", "SW", "Vidsrc", "Streamwish", "Filemoon", "Vidhide", "Netu", "Voesx", "Streamtape"]
    sorted_dict = {}
    for lang, sources_list in sources_dict.items():
        sorted_list = sorted(
            sources_list, 
            key=lambda x: server_preference.index(x.get('server_name')) if x.get('server_name') in server_preference else len(server_preference)
        )
        sorted_dict[lang] = sorted_list
    return sorted_dict

def normalize_text(text):
    """Normaliza texto para búsquedas, quitando tildes y caracteres especiales."""
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', '', text.lower())
    return text

# -----------------------------------------------------------------
# 3. VISTAS PRINCIPALES DE PÁGINAS (HTML)
# -----------------------------------------------------------------
def home(request):
    """Página principal con las últimas publicaciones."""
    latest_content, has_more = data_manager.get_paginated_content('all', page=1, per_page=40)
    context = {'content': latest_content, 'page_title': 'Últimas Novedades', 'content_type': 'all', 'has_more': has_more}
    return render(request, 'core/home.html', context)

def movie_catalog(request):
    """Catálogo de todas las películas."""
    movies, has_more = data_manager.get_paginated_content('movies', page=1, per_page=40)
    context = {'content': movies, 'page_title': 'Películas', 'content_type': 'movies', 'has_more': has_more}
    return render(request, 'core/home.html', context)

def series_catalog(request):
    """Catálogo de todas las series."""
    series, has_more = data_manager.get_paginated_content('series', page=1, per_page=40)
    context = {'content': series, 'page_title': 'Series', 'content_type': 'series', 'has_more': has_more}
    return render(request, 'core/home.html', context)

def anime_catalog(request):
    """Catálogo de todos los animes."""
    animes, has_more = data_manager.get_paginated_content('anime', page=1, per_page=40)
    context = {'content': animes, 'page_title': 'Anime', 'content_type': 'anime', 'has_more': has_more}
    return render(request, 'core/home.html', context)

def content_detail(request, content_id, content_type):
    """Página de detalle para películas, series y anime."""
    content = None
    if content_type == 'movie':
        content = data_manager.find_movie_by_id(content_id)
    elif content_type in ['series', 'anime']:
        content = data_manager.find_series_by_id(content_id)

    if not content:
        # Intenta buscar en el otro tipo por si la URL es incorrecta
        if content_type != 'movie': content = data_manager.find_movie_by_id(content_id)
        if content_type == 'movie': content = data_manager.find_series_by_id(content_id)
    
    if not content: raise Http404("Contenido no encontrado")

    real_content_type = 'movie' if content.get('type') == 'Película' else content.get('type', 'series').lower()

    sources_by_lang = {}
    if real_content_type == 'movie':
        for source in content.get('sources', []):
            lang = source.get('language', 'Idioma Desconocido')
            if lang not in sources_by_lang: sources_by_lang[lang] = []
            sources_by_lang[lang].append(source)
        
        sources_by_lang = sort_sources_by_preference(sources_by_lang)
        sources_by_lang = get_sorted_sources(sources_by_lang)
    
    overview_snippet = (content['overview'][:155] + '...') if len(content.get('overview', '')) > 155 else content.get('overview', '')
    meta_description = f"Mira {content['title']} online. Sinopsis: {overview_snippet}"
    
    context = {
        'content': content, 'page_title': content['title'],
        'sources_by_lang': sources_by_lang, 'is_movie': real_content_type == 'movie',
        'content_type': real_content_type, 'meta_description': meta_description,
    }
    return render(request, 'core/detail_page.html', context)

def episode_player_view(request, content_id, season_number, episode_number):
    """Página del reproductor de episodios para series y animes."""
    content = data_manager.find_series_by_id(content_id)
    if not content: raise Http404("Serie o anime no encontrado")

    current_episode, prev_link, next_link = None, None, None
    all_episodes_flat = []
    if content.get('seasons'):
        for season in content['seasons']:
            if season.get('episodes'):
                for episode in season['episodes']:
                    all_episodes_flat.append({'series_id': content_id, 'season_number': season.get('season_number'), 'episode_number': episode.get('episode_number'), 'data': episode})

    url_name_base = 'anime_episode_player' if content.get('type') == 'Anime' else 'series_episode_player'
    
    for i, ep_flat in enumerate(all_episodes_flat):
        if ep_flat['season_number'] == season_number and ep_flat['episode_number'] == episode_number:
            current_episode = ep_flat['data']
            if i > 0: prev_link = reverse(url_name_base, args=[all_episodes_flat[i - 1]['series_id'], all_episodes_flat[i - 1]['season_number'], all_episodes_flat[i - 1]['episode_number']])
            if i < len(all_episodes_flat) - 1: next_link = reverse(url_name_base, args=[all_episodes_flat[i + 1]['series_id'], all_episodes_flat[i + 1]['season_number'], all_episodes_flat[i + 1]['episode_number']])
            break

    if not current_episode: raise Http404("Episodio no encontrado")

    sources_by_lang = {}
    for source in current_episode.get('sources', []):
        lang = source.get('language', 'Idioma Desconocido')
        if lang not in sources_by_lang: sources_by_lang[lang] = []
        sources_by_lang[lang].append(source)

    sources_by_lang = sort_sources_by_preference(sources_by_lang)
    sources_by_lang = get_sorted_sources(sources_by_lang)

    detail_url_name = 'anime_detail' if content.get('type') == 'Anime' else 'series_detail'
    
    context = {
        'series': content, 'episode': current_episode, 'season_number': season_number,
        'episode_number': episode_number, 'page_title': f"{content['title']} - T{season_number}:E{episode_number}",
        'sources_by_lang': sources_by_lang, 'enlace_anterior': prev_link, 'enlace_siguiente': next_link,
        'enlace_lista_episodios': reverse(detail_url_name, args=[content_id])
    }
    return render(request, 'core/episode_player.html', context)


# -----------------------------------------------------------------
# 4. VISTAS DE API Y UTILIDADES (JSON / XML)
# -----------------------------------------------------------------
def search(request):
    """Vista para la funcionalidad de búsqueda."""
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        normalized_query = normalize_text(query)
        for item in data_manager.get_all_content():
            normalized_title = normalize_text(item['title'])
            if normalized_title.startswith(normalized_query) or any(word.startswith(normalized_query) for word in normalized_title.split()):
                results.append(item)
    context = {'content': results, 'page_title': f'Resultados para "{query}"' if query else 'Búsqueda', 'is_search': True, 'query': query}
    return render(request, 'core/home.html', context)

def load_more(request):
    """API para la paginación infinita."""
    page = int(request.GET.get('page', 2))
    content_type = request.GET.get('type', 'all')
    items, has_more = data_manager.get_paginated_content(content_type, page=page, per_page=40) 
    return JsonResponse({'items': items, 'has_more': has_more})

def sitemap_view(request):
    """Genera el sitemap.xml."""
    all_content = data_manager.get_all_content()
    urls = [
        request.build_absolute_uri(reverse('home')),
        request.build_absolute_uri(reverse('movie_catalog')),
        request.build_absolute_uri(reverse('series_catalog')),
        request.build_absolute_uri(reverse('anime_catalog'))
    ]
    for item in all_content:
        url_name = ''
        if item['type'] == 'Película': url_name = 'movie_detail'
        elif item['type'] == 'Serie': url_name = 'series_detail'
        elif item['type'] == 'Anime': url_name = 'anime_detail'
        if url_name: urls.append(request.build_absolute_uri(reverse(url_name, args=[item['id']])))
    
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for url in urls: sitemap_content += f'<url><loc>{url}</loc></url>'
    sitemap_content += '</urlset>'
    return HttpResponse(sitemap_content, content_type='application/xml')

def stream_proxy_view(request, b64_url):
    """Proxy para reescribir manifiestos M3U8 y evitar bloqueos de Referer."""
    print("\n--- INICIO PETICIÓN PROXY ---")
    try:
        real_url = base64.urlsafe_b64decode(b64_url.encode()).decode()
        print(f"[PROXY] URL decodificada: {real_url[:120]}...")
        
        referer_domain = '/'.join(real_url.split('/')[:3])
        is_m3u8 = '.m3u8' in real_url
        
        if is_m3u8:
            response = requests.get(real_url, headers={'Referer': referer_domain})
            response.raise_for_status()

            content = response.text
            new_content = []
            
            for line in content.splitlines():
                if not line.strip() or line.strip().startswith('#'):
                    new_content.append(line)
                else:
                    absolute_line_url = urljoin(real_url, line.strip())
                    b64_line_url = base64.urlsafe_b64encode(absolute_line_url.encode()).decode()
                    proxy_line_url = request.build_absolute_uri(reverse('stream_proxy', args=[b64_line_url]))
                    new_content.append(proxy_line_url)
            
            final_m3u8 = '\n'.join(new_content)
            print("--- FIN PETICIÓN PROXY (ÉXITO M3U8) ---")
            return HttpResponse(final_m3u8, content_type='application/vnd.apple.mpegurl', status=response.status_code)
        else: # Es un segmento .ts u otro recurso, redirigir directamente
            print("--- FIN PETICIÓN PROXY (REDIRECCIÓN) ---")
            return HttpResponseRedirect(real_url)
    except Exception as e:
        print(f"[PROXY ERROR] Excepción: {type(e).__name__}: {e}")
        print("--- FIN PETICIÓN PROXY (ERROR) ---")
        return HttpResponse(f"Error en el proxy: {e}", status=500)

# -----------------------------------------------------------------
# 5. ¡NUEVA API DE RESOLUCIÓN DE ENLACES!
# -----------------------------------------------------------------
RESOLVER_MAP = {
    'streamwish': resolver.get_m3u8_from_streamwish,
    'sw': resolver.get_m3u8_from_streamwish,
    'filemoon': resolver.get_m3u8_from_filemoon,
    'vidhide': resolver.get_m3u8_from_vidhide,
    'voesx': resolver.get_m3u8_from_voesx,
}

@csrf_exempt
def resolve_source_api(request, server_name, source_id):
    """
    API endpoint que resuelve un enlace de embed en tiempo real usando ScraperAPI.
    """
    print(f"--- [API RESOLVER] Petición para: {server_name} con ID: {source_id} ---")
    server_name_lower = server_name.lower()
    resolver_function = RESOLVER_MAP.get(server_name_lower)
    
    if not resolver_function:
        print(f"--- [API RESOLVER] Error: Servidor '{server_name}' no soportado.")
        return JsonResponse({'success': False, 'error': f'Servidor "{server_name}" no soportado.'}, status=400)

    m3u8_url = resolver_function(source_id)
    
    if m3u8_url:
        print(f"--- [API RESOLVER] Éxito. M3U8 encontrado: {m3u8_url[:100]}...")
        return JsonResponse({'success': True, 'url': m3u8_url})
    else:
        print(f"--- [API RESOLVER] Fallo. No se pudo resolver la fuente.")
        return JsonResponse({'success': False, 'error': f'No se pudo resolver la fuente para {server_name}.'}, status=404)