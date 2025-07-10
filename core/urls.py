# Archivo: core/urls.py (VERSIÓN CORREGIDA Y FINAL)

from django.urls import path, register_converter
from . import views

# Este converter no se usa en las rutas actuales, pero lo dejamos por si acaso.
class IntOrSlugConverter:
    regex = '[0-9]+(-[a-zA-Z0-9_]+)?'
    def to_python(self, value):
        try: return int(value)
        except ValueError: return value
    def to_url(self, value): return str(value)

register_converter(IntOrSlugConverter, 'int-or-slug')

urlpatterns = [
    # URLs de las páginas principales
    path('', views.home, name='home'),
    path('peliculas/', views.movie_catalog, name='movie_catalog'),
    path('series/', views.series_catalog, name='series_catalog'),
    path('anime/', views.anime_catalog, name='anime_catalog'),
    
    # URLs de las páginas de detalle
    path('pelicula/<int:content_id>/', views.content_detail, {'content_type': 'movie'}, name='movie_detail'),
    path('serie/<int:content_id>/', views.content_detail, {'content_type': 'series'}, name='series_detail'),
    path('anime/<int:content_id>/', views.content_detail, {'content_type': 'anime'}, name='anime_detail'),

    # URLs de los reproductores de episodios
    path('serie/<int:content_id>/temporada/<int:season_number>/episodio/<int:episode_number>/', 
        views.episode_player_view, name='series_episode_player'),
    path('anime/<int:content_id>/temporada/<int:season_number>/episodio/<int:episode_number>/', 
        views.episode_player_view, name='anime_episode_player'),

    # URLs de utilidades y API
    path('buscar/', views.search, name='search'),
    path('cargar-mas/', views.load_more, name='load_more'),
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    
    # --- RUTA DE LA API CORREGIDA ---
    # Apunta a la nueva función 'resolve_source_api' en views.py
    path('api/v1/resolve/<str:server_name>/<str:source_id>/', views.resolve_source_api, name='resolve_source_api'),

    # Ruta del proxy de M3U8 (se mantiene igual)
    path('proxy-stream/<path:b64_url>/', views.stream_proxy_view, name='stream_proxy'),
]