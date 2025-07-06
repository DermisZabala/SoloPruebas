# Archivo: core/admin.py

from django.contrib import admin
from .models import Movie, VideoSource

# Esta clase nos permite ver las fuentes de video directamente en la página de la película
class VideoSourceInline(admin.TabularInline):
    model = VideoSource
    extra = 1  # Cuántos campos de fuente vacíos mostrar
    fields = ('language', 'server_name', 'embed_url') # Campos a mostrar
    readonly_fields = () # Si quieres hacer algún campo de solo lectura

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'tmdb_id') # Columnas a mostrar en la lista de películas
    list_filter = ('release_date',) # Permite filtrar por fecha de estreno
    search_fields = ('title', 'tmdb_id') # Añade una barra de búsqueda para título y tmdb_id
    
    # Aquí es donde le decimos a Django que muestre las fuentes de video dentro de la película
    inlines = [VideoSourceInline]

@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    # También registramos VideoSource por separado por si quieres gestionarlos directamente
    list_display = ('movie', 'language', 'server_name')
    list_filter = ('language', 'server_name')
    search_fields = ('movie__title',)