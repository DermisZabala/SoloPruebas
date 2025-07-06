# Archivo: core/management/commands/add_season.py (VERSIÓN MODIFICADA)

from django.core.management.base import BaseCommand, CommandError
from ._utils import (
    get_data_file_path, load_local_data, save_local_data, update_data_list,
    get_anime_details, build_base_anime_json,
    scrape_episodes_from_page, scrape_animeflv_page_details, find_animeflv_page_data
)

class Command(BaseCommand):
    help = 'Añade o actualiza una temporada a una ficha de anime existente usando una URL directa de AnimeFLV.'

    def add_arguments(self, parser):
        parser.add_argument('root_anilist_id', type=int, help='El ID de AniList del anime RAÍZ (la ficha principal).')
        
        # --- ARGUMENTOS MODIFICADOS ---
        parser.add_argument('--season-id', type=int, required=True, help='El ID de AniList de la temporada específica que estás añadiendo.')
        parser.add_argument('--url', type=str, required=True, help='La URL completa de la temporada en AnimeFLV.')
        # --- FIN DE MODIFICACIONES ---

        parser.add_argument('--file-index', type=int, choices=[1, 2, 3], required=True, help='Índice del archivo JSON.')
        parser.add_argument('--display-title', type=str, required=True, help='Nombre para el botón en la web (Ej: "Temporada 2").')
        parser.add_argument('--force', action='store_true', help='Fuerza el re-scrapeo y la actualización de una temporada existente.')

    def handle(self, *args, **kwargs):
        root_id = kwargs['root_anilist_id']
        season_id = kwargs['season_id'] # Nuevo argumento
        animeflv_url = kwargs['url'] # Nuevo argumento
        file_index = kwargs['file_index']
        display_title = kwargs['display_title']
        force_update = kwargs['force']
        
        target_file = get_data_file_path(file_index)
        local_data = load_local_data(target_file)
        
        anime_json = next((item for item in local_data.get('anime', []) if item.get('id') == root_id), None)
        
        # La lógica para crear la ficha raíz si no existe se mantiene igual.
        if not anime_json:
            self.stdout.write(self.style.WARNING(f"No se encontró el anime con ID {root_id}. Se creará una nueva ficha."))
            anime_details = get_anime_details(root_id)
            if not anime_details: raise CommandError(f"No se pudo obtener info para ID {root_id}.")
            
            # Para la sinopsis, buscamos la página pero no scrapeamos los episodios aún
            page_data = find_animeflv_page_data(anime_details)
            if page_data:
                details = scrape_animeflv_page_details(page_data['url'])
                if details['synopsis']:
                    anime_details['overview'] = details['synopsis']
            
            anime_json = build_base_anime_json(anime_details)
            local_data['anime'].append(anime_json)
        
        # La lógica para comprobar si la temporada ya existe se mantiene.
        existing_season = next((s for s in anime_json.get('seasons', []) if s.get('anilist_id') == season_id), None)
        if existing_season and not force_update:
            self.stdout.write(self.style.ERROR(f"La temporada con ID {season_id} ya existe en esta ficha. Usa --force para sobreescribirla."))
            return

        # Obtenemos los detalles de la temporada de AniList para tener su título canónico.
        season_data = get_anime_details(season_id)
        if not season_data: raise CommandError(f"No se pudo obtener info de la temporada con ID {season_id}.")
            
        self.stdout.write(self.style.NOTICE(f"\n--- Procesando temporada: '{season_data['title']}' ---"))
        
        # --- LÓGICA DE SCRAPING MODIFICADA ---
        # Ya no buscamos la página, usamos la URL proporcionada directamente.
        self.stdout.write(self.style.NOTICE(f"Scrapeando desde la URL proporcionada: {animeflv_url}"))
        
        # El primer valor (sinopsis) no se usa aquí, así que lo ignoramos con _
        _, scraped_episodes = scrape_episodes_from_page(animeflv_url)
        # --- FIN DE LA MODIFICACIÓN ---
        
        if not scraped_episodes:
            self.stdout.write(self.style.WARNING("No se encontraron episodios en la URL. No se realizará ningún cambio."))
            return

        # La lógica para añadir o actualizar la temporada se mantiene, pero ahora guardamos la URL.
        if existing_season:
            existing_season['episodes'] = scraped_episodes
            existing_season['display_title'] = display_title
            existing_season['title'] = season_data['title']
            existing_season['animeflv_url'] = animeflv_url # Guardamos la URL
            self.stdout.write(self.style.SUCCESS(f"  -> Temporada '{display_title}' forzada a actualizar."))
        else:
            next_season_number = len(anime_json.get('seasons', [])) + 1
            season_to_add = {
                "anilist_id": season_data['id'], 
                "season_number": next_season_number, 
                "title": season_data['title'], 
                "display_title": display_title, 
                "episodes": scraped_episodes,
                "animeflv_url": animeflv_url # Guardamos la URL
            }
            anime_json['seasons'].append(season_to_add)
            self.stdout.write(self.style.SUCCESS(f"  -> Nueva temporada '{display_title}' añadida."))

        # Re-ordenamos y guardamos.
        anime_json['seasons'].sort(key=lambda s: s.get('season_number', 0))
        update_data_list(local_data['anime'], anime_json)
        save_local_data(local_data, target_file)
        self.stdout.write(self.style.SUCCESS(f"\n¡Éxito! El anime '{anime_json['title']}' ha sido actualizado."))