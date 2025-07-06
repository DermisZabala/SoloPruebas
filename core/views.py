# Archivo: core/views.py (COMPLETO Y FINAL)
from django.shortcuts import render, reverse
from django.http import Http404, JsonResponse, HttpResponse
from . import data_manager
import unicodedata
import re

# =================================================================
# === NUEVA FUNCIÓN DE AYUDA PARA ORDENAR IDIOMAS ===
# =================================================================
def get_sorted_sources(sources_dict):
    """
    Toma el diccionario de fuentes y devuelve una lista de tuplas
    ordenada según una prioridad de idiomas predefinida.
    """
    # Define aquí el orden que SIEMPRE quieres.
    # "Latino" y "Español" primero, luego "Subtitulado".
    language_priority = ["Latino", "Español", "Subtitulado"]
    
    sorted_list = []
    
    # 1. Añade los idiomas prioritarios en el orden correcto.
    for lang in language_priority:
        if lang in sources_dict:
            sorted_list.append((lang, sources_dict[lang]))
            
    # 2. (Opcional pero recomendado) Añade cualquier otro idioma que no esté en la lista de prioridad al final.
    for lang, sources in sources_dict.items():
        if lang not in language_priority:
            sorted_list.append((lang, sources))
            
    return sorted_list
# =================================================================


def sort_sources_by_preference(sources_dict):
    """
    Ordena las fuentes de video dentro de cada idioma según una lista de preferencia.
    (Esta función no cambia)
    """
    server_preference = [
        "MEGA",
        "SW",
        "Vidsrc",
        "Streamwish",
        "Filemoon",
        "Vidhide",
        "Netu",
        "Voesx",
        "Streamtape",
    ]
    sorted_dict = {}
    for lang, sources_list in sources_dict.items():
        sorted_list = sorted(
            sources_list, 
            key=lambda x: server_preference.index(x.get('server_name')) 
                        if x.get('server_name') in server_preference 
                        else len(server_preference)
        )
        sorted_dict[lang] = sorted_list
    return sorted_dict


def home(request):
    """Página principal con las últimas 30 publicaciones."""
    latest_content, has_more = data_manager.get_paginated_content('all', page=1, per_page=40)
    context = { 'content': latest_content, 'page_title': 'Últimas Novedades', 'content_type': 'all', 'has_more': has_more }
    return render(request, 'core/home.html', context)

def movie_catalog(request):
    """Catálogo de todas las películas."""
    movies, has_more = data_manager.get_paginated_content('movies', page=1, per_page=40)
    context = { 'content': movies, 'page_title': 'Películas', 'content_type': 'movies', 'has_more': has_more }
    return render(request, 'core/home.html', context)

def series_catalog(request):
    """Catálogo de todas las series."""
    series, has_more = data_manager.get_paginated_content('series', page=1, per_page=40)
    context = { 'content': series, 'page_title': 'Series', 'content_type': 'series', 'has_more': has_more }
    return render(request, 'core/home.html', context)

def anime_catalog(request):
    """Catálogo de todos los animes."""
    animes, has_more = data_manager.get_paginated_content('anime', page=1, per_page=40)
    context = { 'content': animes, 'page_title': 'Anime', 'content_type': 'anime', 'has_more': has_more }
    return render(request, 'core/home.html', context)

def content_detail(request, content_id, content_type):
    """Página de detalle para películas."""
    content = None
    if content_type == 'movie':
        content = data_manager.find_movie_by_id(content_id)
    elif content_type in ['series', 'anime']:
        content = data_manager.find_series_by_id(content_id)
    if not content:
        if content_type != 'movie': content = data_manager.find_movie_by_id(content_id)
        if content_type == 'movie': content = data_manager.find_series_by_id(content_id)
    if not content: raise Http404("Contenido no encontrado")

    real_content_type = 'movie' if content.get('type') == 'Película' else content.get('type', 'series').lower()

    # MODIFICACIÓN PARA PELÍCULAS
    sources_by_lang = {}
    if real_content_type == 'movie':
        for source in content.get('sources', []):
            lang = source.get('language', 'Idioma Desconocido')
            if lang not in sources_by_lang:
                sources_by_lang[lang] = []
            sources_by_lang[lang].append(source)
        
        sources_by_lang = sort_sources_by_preference(sources_by_lang)
        # AHORA PASAMOS EL DICCIONARIO A LA NUEVA FUNCIÓN PARA ORDENARLO
        sources_by_lang = get_sorted_sources(sources_by_lang)
    
    overview_snippet = (content['overview'][:155] + '...') if len(content['overview']) > 155 else content['overview']
    meta_description = f"Mira {content['title']} online. Sinopsis: {overview_snippet}"
    
    context = {
        'content': content,
        'page_title': content['title'],
        'sources_by_lang': sources_by_lang, # Ya va ordenado
        'is_movie': real_content_type == 'movie',
        'content_type': real_content_type,
        'meta_description': meta_description,
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

    # MODIFICACIÓN PARA EPISODIOS
    sources_by_lang = {}
    for source in current_episode.get('sources', []):
        lang = source.get('language', 'Idioma Desconocido')
        if lang not in sources_by_lang:
            sources_by_lang[lang] = []
        sources_by_lang[lang].append(source)

    sources_by_lang = sort_sources_by_preference(sources_by_lang)
    # AHORA PASAMOS EL DICCIONARIO A LA NUEVA FUNCIÓN PARA ORDENARLO
    sources_by_lang = get_sorted_sources(sources_by_lang)

    detail_url_name = 'anime_detail' if content.get('type') == 'Anime' else 'series_detail'
    
    context = {
        'series': content, 'episode': current_episode, 'season_number': season_number,
        'episode_number': episode_number, 'page_title': f"{content['title']} - T{season_number}:E{episode_number}",
        'sources_by_lang': sources_by_lang, # Ya va ordenado
        'enlace_anterior': prev_link, 'enlace_siguiente': next_link,
        'enlace_lista_episodios': reverse(detail_url_name, args=[content_id])
    }
    return render(request, 'core/episode_player.html', context)


# --- El resto de las vistas (load_more, search, sitemap) no cambian ---
def load_more(request):
    page = int(request.GET.get('page', 2))
    content_type = request.GET.get('type', 'all')
    items, has_more = data_manager.get_paginated_content(content_type, page=page, per_page=40) 
    return JsonResponse({'items': items, 'has_more': has_more})

def normalize_text(text):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', '', text.lower())
    return text

def search(request):
    query = request.GET.get('q', '').strip()
    all_content = data_manager.get_all_content()
    results = []
    if query:
        normalized_query = normalize_text(query)
        for item in all_content:
            normalized_title = normalize_text(item['title'])
            if normalized_title.startswith(normalized_query) or \
               any(word.startswith(normalized_query) for word in normalized_title.split()):
                results.append(item)
    context = {'content': results, 'page_title': f'Resultados para "{query}"' if query else 'Búsqueda', 'is_search': True, 'query': query}
    return render(request, 'core/home.html', context)

def sitemap_view(request):
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



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import base64
from django.http import StreamingHttpResponse
from . import resolver # Importamos nuestro nuevo archivo

# Archivo: core/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import resolver # ...y otros imports que ya tienes

# ... (El resto de tus vistas se quedan igual) ...

@csrf_exempt
def resolve_source_view(request, server_name, source_id):
    # """
    # API endpoint con depuradores para encontrar el problema.
    # """
    # # === DEPURADOR 1: ¿Llega la petición a la vista correcta? ===
    # print("==========================================================")
    # print(f"[API DEBUG] Petición RECIBIDA a 'resolve_source_view'.")
    # print(f"[API DEBUG] -> Método HTTP: {request.method}")
    # print(f"[API DEBUG] -> server_name capturado: '{server_name}' (Tipo: {type(server_name)})")
    # print(f"[API DEBUG] -> source_id capturado: '{source_id}' (Tipo: {type(source_id)})")
    
    # resolved_url = None
    # server_name_lower = server_name.lower()
    
    # # === DEPURADOR 2: ¿Estamos entrando en el `if` correcto? ===
    # if server_name_lower == 'streamwish' or server_name_lower == 'sw':
    #     print(f"[API DEBUG] Coincidencia encontrada. Llamando a resolver.get_m3u8_from_streamwish...")
    #     resolved_url = resolver.get_m3u8_from_streamwish(source_id)
        
    # elif server_name_lower == 'filemoon':
    #     print(f"[API DEBUG] Coincidencia encontrada. Llamando a resolver.get_m3u8_from_filemoon...")
    #     resolved_url = resolver.get_m3u8_from_filemoon(source_id)
        
    # elif server_name_lower == 'vidhide':
    #     print(f"[API DEBUG] Coincidencia encontrada. Llamando a resolver.get_m3u8_from_vidhide...")
    #     resolved_url = resolver.get_m3u8_from_vidhide(source_id)
    
    # # --- AÑADE ESTE ELIF PARA VOESX ---
    # elif server_name_lower == 'voesx':
    #     print(f"[API DEBUG] Coincidencia encontrada. Llamando a resolver.get_m3u8_from_voesx...")
    #     resolved_url = resolver.get_m3u8_from_voesx(source_id)
    
    # else:
    #     # === DEPURADOR 3: Si no entra en ningún if, ¿por qué? ===
    #     print(f"[API DEBUG] ERROR: El server_name '{server_name_lower}' no coincide con ninguna opción.")
    #     return JsonResponse({'success': False, 'error': f'Servidor "{server_name}" no soportado.'}, status=400)

    # # === DEPURADOR 4: ¿Qué nos devuelve el resolver? ===
    # print(f"[API DEBUG] El 'resolver' devolvió: {resolved_url}")
    # print("==========================================================")
    
    # # === ESTA ES LA PARTE A REEMPLAZAR ===
    # if resolved_url:
    #     # Codificamos la URL real del M3U8
    #     b64_m3u8_url = base64.urlsafe_b64encode(resolved_url.encode()).decode()
        
    #     # Construimos la URL de NUESTRO PROXY
    #     proxy_url = request.build_absolute_uri(reverse('stream_proxy', args=[b64_m3u8_url]))
        
    #     return JsonResponse({'success': True, 'm3u8_url': proxy_url})
    # else:
    #     return JsonResponse({'success': False, 'error': f'No se pudo resolver la fuente para {server_name}. Puede que el enlace esté caído.'}, status=404)
    pass


# En core/views.py

# Asegúrate de tener estos imports al principio del archivo
import requests
import base64
from django.http import HttpResponse, HttpResponseRedirect
from urllib.parse import urljoin # <-- ¡NUEVO IMPORT!

# ... (el resto de tus vistas se quedan igual) ...

# ===== REEMPLAZA TU VISTA DE PROXY CON ESTA VERSIÓN FINAL =====
def stream_proxy_view(request, b64_url):
    print("\n----------------- INICIO PETICIÓN PROXY -----------------")
    try:
        print(f"[PROXY DEBUG 1] Recibida b64_url: {b64_url[:120]}...")
        real_url = base64.urlsafe_b64decode(b64_url.encode()).decode()
        print(f"[PROXY DEBUG 2] URL decodificada: {real_url[:120]}...")
        
        referer_domain = '/'.join(real_url.split('/')[:3])
        print(f"[PROXY DEBUG 3] Referer a usar: {referer_domain}")

        is_m3u8 = real_url.endswith('.m3u8')
        is_ts = real_url.endswith('.ts')
        print(f"[PROXY DEBUG 4] Tipo de archivo detectado: M3U8={is_m3u8}, TS={is_ts}")
        
        if is_m3u8:
            print("[PROXY DEBUG 5a] Manejando como archivo M3U8.")
            response = requests.get(real_url, headers={'Referer': referer_domain})
            print(f"[PROXY DEBUG 6a] Petición a servidor externo devolvió: {response.status_code}")
            response.raise_for_status()

            content = response.content.decode('utf-8')
            new_content = []
            
            print("[PROXY DEBUG 7a] Reescribiendo contenido del M3U8...")
            for i, line in enumerate(content.splitlines()):
                line = line.strip()
                if not line or line.startswith('#'):
                    new_content.append(line)
                else:
                    absolute_line_url = urljoin(real_url, line)
                    b64_line_url = base64.urlsafe_b64encode(absolute_line_url.encode()).decode()
                    proxy_line_url = request.build_absolute_uri(reverse('stream_proxy', args=[b64_line_url]))
                    new_content.append(proxy_line_url)
                    if i < 5: # Solo muestra las primeras 5 URLs reescritas para no saturar el log
                        print(f"    -> Línea original: {line}")
                        print(f"    -> URL reescrita: {proxy_line_url[:120]}...")
            
            final_m3u8 = '\n'.join(new_content)
            print("[PROXY DEBUG 8a] Devolviendo M3U8 modificado al cliente.")
            print("----------------- FIN PETICIÓN PROXY (ÉXITO M3U8) -----------------\n")
            return HttpResponse(final_m3u8, content_type='application/vnd.apple.mpegurl', status=response.status_code)
        
        else: # Asumimos que es un .ts u otro recurso
            print("[PROXY DEBUG 5b] Manejando como segmento de video (.ts) o recurso. Redirigiendo...")
            print(f"[PROXY DEBUG 6b] Redirigiendo al cliente a: {real_url[:120]}...")
            print("----------------- FIN PETICIÓN PROXY (REDIRECCIÓN) -----------------\n")
            return HttpResponseRedirect(real_url)

    except Exception as e:
        print(f"[PROXY DEBUG ERROR] Ha ocurrido una excepción: {type(e).__name__}: {e}")
        print("----------------- FIN PETICIÓN PROXY (ERROR) -----------------\n")
        return HttpResponse(f"Error en el proxy: {e}", status=500)