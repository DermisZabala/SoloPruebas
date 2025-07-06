# Archivo: core/management/commands/delete_content.py (VERSIÓN FINAL Y CORREGIDA)

import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Elimina contenido (película, serie o anime) de un archivo JSON específico.'

    def add_arguments(self, parser):
        parser.add_argument('--file-index', type=int, choices=[1, 2, 3], required=True, help='El índice del archivo JSON a usar.')
        parser.add_argument('content_id', type=int, help='El ID del contenido a eliminar (TMDB para movie/series, AniList para anime).')
        parser.add_argument('--type', type=str, choices=['movie', 'series', 'anime'], required=True, help="El tipo de contenido a eliminar.")
        parser.add_argument('--season-id', type=int, help='(Opcional) El ID de AniList de la temporada de anime a eliminar.')
        parser.add_argument('--season-number', type=int, help='(Opcional) El número de la temporada de serie a eliminar.')

    def get_data_file_path(self, index):
        """Construye la ruta del archivo basado en el índice."""
        if index not in [1, 2, 3]:
            raise CommandError("El índice del archivo debe ser 1, 2 o 3.")
        return Path(f"C:/mi-json{index}/data{index}.json")

    def load_local_data(self, file_path):
        """Carga datos desde un archivo JSON, manejando errores."""
        if not file_path.exists():
            raise CommandError(f"El archivo de datos '{file_path}' no existe. No hay nada que eliminar.")
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                raise CommandError(f"Error al leer el archivo JSON '{file_path}'. ¿Está corrupto?")

    def save_local_data(self, data, file_path):
        """Guarda los datos en un archivo JSON con formato legible."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.stdout.write(self.style.SUCCESS(f"Datos guardados exitosamente en '{file_path}'"))

    def handle(self, *args, **kwargs):
        """Función principal que orquesta la lógica del comando."""
        file_index = kwargs['file_index']
        content_id = kwargs['content_id']
        content_type = kwargs['type']
        
        target_file = self.get_data_file_path(file_index)
        self.stdout.write(self.style.NOTICE(f"--- Usando archivo de destino: {target_file} ---"))
        local_data = self.load_local_data(target_file)

        if content_type == 'movie':
            self.delete_movie(local_data, content_id)
        elif content_type == 'series':
            season_num_to_delete = kwargs.get('season_number')
            if season_num_to_delete is not None:
                self.delete_series_season(local_data, content_id, season_num_to_delete)
            else:
                self.delete_series(local_data, content_id)
        elif content_type == 'anime':
            season_id_to_delete = kwargs.get('season_id')
            if season_id_to_delete is not None:
                self.delete_anime_season(local_data, content_id, season_id_to_delete)
            else:
                self.delete_anime(local_data, content_id)
        
        self.save_local_data(local_data, target_file)

    def delete_movie(self, data, tmdb_id):
        """Elimina una película del JSON."""
        original_len = len(data.get('movies', []))
        # Aseguramos que ambos sean integers para una comparación segura
        data['movies'] = [m for m in data.get('movies', []) if int(m.get('id', 0)) != int(tmdb_id)]
        
        if len(data.get('movies', [])) < original_len:
            self.stdout.write(self.style.SUCCESS(f"Éxito: Se eliminó la película con ID {tmdb_id}."))
        else:
            self.stdout.write(self.style.WARNING(f"Advertencia: No se encontró ninguna película con el ID {tmdb_id}."))
    
    def delete_series(self, data, tmdb_id):
        """Elimina una serie completa del JSON."""
        original_len = len(data.get('series', []))
        # Aseguramos que ambos sean integers
        data['series'] = [s for s in data.get('series', []) if int(s.get('id', 0)) != int(tmdb_id)]
        
        if len(data.get('series', [])) < original_len:
             self.stdout.write(self.style.SUCCESS(f"Éxito: Se eliminó la serie completa con ID {tmdb_id}."))
        else:
            self.stdout.write(self.style.WARNING(f"Advertencia: No se encontró ninguna serie con el ID {tmdb_id}."))

    def delete_series_season(self, data, tmdb_id, season_number):
        """Elimina una temporada específica de una serie."""
        series_found = next((s for s in data.get('series', []) if int(s.get('id', 0)) == int(tmdb_id)), None)
        if not series_found:
            self.stdout.write(self.style.WARNING(f"Advertencia: No se encontró ninguna serie con el ID {tmdb_id}."))
            return
        
        original_len = len(series_found.get('seasons', []))
        # Aseguramos que ambos sean integers
        series_found['seasons'] = [s for s in series_found.get('seasons', []) if int(s.get('season_number', 0)) != int(season_number)]
        
        if len(series_found.get('seasons', [])) < original_len:
            self.stdout.write(self.style.SUCCESS(f"Éxito: Se eliminó la temporada {season_number} de la serie con ID {tmdb_id}."))
        else:
            self.stdout.write(self.style.WARNING(f"Advertencia: No se encontró la temporada {season_number} en la serie con ID {tmdb_id}."))

    def delete_anime(self, data, anilist_id):
        """Elimina una franquicia de anime completa del JSON."""
        original_len = len(data.get('anime', []))
        # Aseguramos que ambos sean integers
        data['anime'] = [a for a in data.get('anime', []) if int(a.get('id', 0)) != int(anilist_id)]
        
        if len(data.get('anime', [])) < original_len:
            self.stdout.write(self.style.SUCCESS(f"Éxito: Se eliminó el anime completo con ID {anilist_id}."))
        else:
            self.stdout.write(self.style.WARNING(f"Advertencia: No se encontró ningún anime con el ID {anilist_id}."))

    def delete_anime_season(self, data, root_anilist_id, season_anilist_id):
        """Elimina una temporada específica de un anime."""
        anime = next((a for a in data.get('anime', []) if int(a.get('id', 0)) == int(root_anilist_id)), None)
        if not anime:
            self.stdout.write(self.style.WARNING(f"Advertencia: No se encontró el anime con ID raíz {root_anilist_id}."))
            return
        
        original_len = len(anime.get('seasons', []))
        # Aseguramos que ambos sean integers
        anime['seasons'] = [s for s in anime.get('seasons', []) if int(s.get('anilist_id', 0)) != int(season_anilist_id)]
        
        if len(anime.get('seasons', [])) < original_len:
            # Re-indexamos los season_number para que no queden huecos
            for i, season in enumerate(anime['seasons']):
                season['season_number'] = i + 1
            self.stdout.write(self.style.SUCCESS(f"Éxito: Se eliminó la temporada con ID {season_anilist_id} del anime."))
        else:
            self.stdout.write(self.style.WARNING(f"Advertencia: No se encontró la temporada con ID {season_anilist_id} en el anime."))