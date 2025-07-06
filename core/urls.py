# Archivo: core/urls.py
from django.urls import path, register_converter
from . import views

class IntOrSlugConverter:
    regex = '[0-9]+(-[a-zA-Z0-9_]+)?'

    def to_python(self, value):
        try:
            return int(value)
        except ValueError:
            return value

    def to_url(self, value):
        return str(value)

register_converter(IntOrSlugConverter, 'int-or-slug')

urlpatterns = [
    # === ¡AQUÍ ESTÁ LA LÍNEA CORREGIDA! ===
    # Cambiamos <path:source_id> por <str:source_id>
    # También he corregido el "name" para ser más específico
    path('api/resolve/<str:server_name>/<str:source_id>/', views.resolve_source_view, name='resolve_source_view'),
    
    # ... resto de URLs ...
    path('', views.home, name='home'),
    path('peliculas/', views.movie_catalog, name='movie_catalog'),
    path('series/', views.series_catalog, name='series_catalog'),
    path('anime/', views.anime_catalog, name='anime_catalog'),
    
    path('pelicula/<int:content_id>/', views.content_detail, {'content_type': 'movie'}, name='movie_detail'),
    path('serie/<int:content_id>/', views.content_detail, {'content_type': 'series'}, name='series_detail'),
    path('anime/<int:content_id>/', views.content_detail, {'content_type': 'anime'}, name='anime_detail'),

    path('serie/<int:content_id>/temporada/<int:season_number>/episodio/<int:episode_number>/', 
        views.episode_player_view, 
        name='series_episode_player'),
    path('anime/<int:content_id>/temporada/<int:season_number>/episodio/<int:episode_number>/', 
        views.episode_player_view, 
        name='anime_episode_player'),

    path('buscar/', views.search, name='search'),
    path('cargar-mas/', views.load_more, name='load_more'),
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    
    # Esta del proxy la dejamos con <path:...> porque sí necesita capturar barras y caracteres especiales.
    path('proxy-stream/<path:b64_url>/', views.stream_proxy_view, name='stream_proxy'),
]