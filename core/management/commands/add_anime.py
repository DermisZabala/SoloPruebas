# Archivo: core/management/commands/add_anime.py (VERSIÓN MODIFICADA "DOS EN UNO")

from django.core.management.base import BaseCommand, CommandError
from ._utils import (
    get_data_file_path, load_local_data, save_local_data, update_data_list,
    get_all_related_tv_seasons, get_anime_details,
    find_animeflv_page_data, scrape_episodes_from_page
)

class Command(BaseCommand):
    help = 'Añade animes. Modo 1 (default): busca y añade una franquicia entera. Modo 2 (--url): añade una temporada específica desde una URL.'

    def add_arguments(self, parser):
        parser.add_argument('anilist_id', type=int, help="ID de AniList. En modo franquicia, es el ID inicial. En modo URL, es el ID de la temporada específica.")
        parser.add_argument('--file-index', type=int, choices=[1, 2, 3], required=True)
        
        # --- NUEVO ARGUMENTO OPCIONAL ---
        parser.add_argument('--url', type=str, help='(Opcional) URL de AnimeFLV para añadir una temporada específica. Activa el modo de adición única.')
        
    def handle(self, *args, **kwargs):
        start_anilist_id = kwargs['anilist_id']
        file_index = kwargs['file_index']
        specific_url = kwargs.get('url') # Si se proporciona, activa el modo específico

        if specific_url:
            self.handle_specific_anime(start_anilist_id, specific_url, file_index)
        else:
            self.handle_franchise(start_anilist_id, file_index)

    def handle_specific_anime(self, season_id, animeflv_url, file_index):
        """
        Lógica para añadir una única temporada de anime usando una URL directa.
        """
        self.stdout.write(self.style.NOTICE(f"\n--- MODO ESPECÍFICO: Añadiendo anime con ID {season_id} desde URL ---"))
        target_file = get_data_file_path(file_index)
        local_data = load_local_data(target_file)
        
        # Comprobar si ya existe para evitar duplicados
        existing_entry = next((item for item in local_data.get('anime', []) if item.get('id') == season_id), None)
        if existing_entry:
            self.stdout.write(self.style.ERROR(f"ERROR: El anime con ID {season_id} ya existe en el archivo. Use 'add_season --force' o 'delete_content' para modificarlo."))
            return

        # Obtener detalles de AniList para la ficha
        season_details = get_anime_details(season_id)
        if not season_details:
            raise CommandError(f"No se pudieron obtener los detalles de AniList para el ID {season_id}.")
        
        # Scrapear episodios desde la URL proporcionada
        self.stdout.write(f"  -> Scrapeando episodios desde: {animeflv_url}")
        synopsis_es, scraped_episodes = scrape_episodes_from_page(animeflv_url)
        if not scraped_episodes:
            self.stdout.write(self.style.WARNING("  -> No se encontraron episodios en la página. No se añadirá el anime."))
            return

        # Usar el título de AniList como fallback
        final_title = season_details['title_romaji']
        
        # Construir la ficha del anime
        anime_entry = {
            "id": season_id,
            "imdb_id": None,
            "title": final_title,
            "original_title": season_details['title_romaji'],
            "overview": synopsis_es if synopsis_es else season_details['overview'],
            "poster_path": season_details['poster_path'],
            "backdrop_path": season_details['backdrop_path'],
            "type": "Anime",
            "release_date": f"{season_details['year']}-01-01" if season_details.get('year') else None,
            "rating": "N/A",
            "genres": season_details['genres'],
            "cast": [],
            "animeflv_url": animeflv_url,
            "seasons": [
                {
                    "anilist_id": season_id,
                    "season_number": 1,
                    "title": final_title,
                    "display_title": "Episodios",
                    "episodes": scraped_episodes
                }
            ]
        }

        update_data_list(local_data['anime'], anime_entry)
        save_local_data(local_data, target_file)
        self.stdout.write(self.style.SUCCESS(f"\n¡Éxito! El anime '{final_title}' ha sido añadido al archivo '{target_file.name}'."))


    def handle_franchise(self, start_anilist_id, file_index):
        """
        Lógica original para buscar y añadir todas las temporadas de una franquicia.
        """
        self.stdout.write(self.style.NOTICE(f"\n--- MODO FRANQUICIA: Buscando animes relacionados con ID {start_anilist_id} ---"))
        target_file = get_data_file_path(file_index)
        local_data = load_local_data(target_file)
        
        existing_url_map = {item['animeflv_url']: item['id'] for item in local_data.get('anime', []) if item.get('animeflv_url')}
        processed_in_this_run = set()
        
        tv_seasons = get_all_related_tv_seasons(start_anilist_id)
        if not tv_seasons:
            raise CommandError("No se encontraron temporadas de TV en esta franquicia.")
        
        self.stdout.write(self.style.SUCCESS(f"Se encontraron {len(tv_seasons)} temporadas de TV para procesar."))
        
        for i, season_info in enumerate(tv_seasons):
            season_id = season_info['id']
            self.stdout.write(self.style.NOTICE(f"\n--- Procesando Temporada de TV {i+1}/{len(tv_seasons)}: '{season_info['title']}' (ID: {season_id}) ---"))

            existing_entry = next((item for item in local_data.get('anime', []) if item.get('id') == season_id), None)
            if existing_entry:
                self.stdout.write(self.style.SUCCESS(f"  -> Esta temporada (ID: {season_id}) ya existe en el archivo. Omitiendo."))
                if existing_entry.get('animeflv_url'):
                    processed_in_this_run.add(existing_entry.get('animeflv_url'))
                continue

            season_details = get_anime_details(season_id)
            if not season_details:
                self.stdout.write(self.style.WARNING(f"  -> No se pudieron obtener los detalles de AniList. Omitiendo."))
                continue

            page_data = find_animeflv_page_data(season_details)
            if not page_data:
                self.stdout.write(self.style.WARNING("  -> No se pudo asociar con una página de AnimeFLV. Omitiendo."))
                continue
            
            animeflv_url = page_data['url']

            if animeflv_url in existing_url_map:
                 self.stdout.write(self.style.ERROR(f"  -> ¡CONFLICTO! La URL '{animeflv_url}' ya está en uso por el anime con ID {existing_url_map[animeflv_url]}. Omitiendo."))
                 continue

            if animeflv_url in processed_in_this_run:
                self.stdout.write(self.style.WARNING(f"  -> CONFLICTO: La URL '{animeflv_url}' ya fue usada por otra temporada en esta misma ejecución. Omitiendo."))
                continue

            processed_in_this_run.add(animeflv_url)
            synopsis_es, scraped_episodes = scrape_episodes_from_page(animeflv_url)

            if not scraped_episodes:
                self.stdout.write(self.style.WARNING(f"  -> No se encontraron episodios en la página. Omitiendo."))
                continue

            final_title = page_data['title'] if page_data.get('title') else season_details['title_romaji']
            
            anime_entry = {
                "id": season_id, "imdb_id": None, "title": final_title,
                "original_title": season_details['title_romaji'],
                "overview": synopsis_es if synopsis_es else season_details['overview'],
                "poster_path": season_details['poster_path'], "backdrop_path": season_details['backdrop_path'],
                "type": "Anime", "release_date": f"{season_details['year']}-01-01" if season_details.get('year') else None,
                "rating": "N/A", "genres": season_details['genres'], "cast": [], "animeflv_url": animeflv_url,
                "seasons": [{"anilist_id": season_id, "season_number": 1, "title": final_title, "display_title": "Episodios", "episodes": scraped_episodes}]
            }

            update_data_list(local_data['anime'], anime_entry)
            self.stdout.write(self.style.SUCCESS(f"  -> NUEVA temporada '{final_title}' procesada y añadida."))

        save_local_data(local_data, target_file)
        self.stdout.write(self.style.SUCCESS(f"\n¡Éxito! El archivo '{target_file.name}' ha sido actualizado."))