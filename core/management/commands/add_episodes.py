# Archivo: core/management/commands/add_episodes.py (VERSIÓN FINAL Y COMPLETA)

from django.core.management.base import BaseCommand, CommandError
from ._utils import (
    get_data_file_path, load_local_data, save_local_data, update_data_list,
    get_anime_details, build_base_anime_json,
    scrape_episode_sources, find_animeflv_page_data, scrape_animeflv_page_details
)

class Command(BaseCommand):
    help = 'Añade o actualiza un rango de episodios a una temporada. Crea la ficha si no existe.'

    def add_arguments(self, parser):
        parser.add_argument('root_anilist_id', type=int, help='El ID de AniList del anime RAÍZ.')
        parser.add_argument('season_anilist_id', nargs='?', type=int, default=None, help='(Opcional) ID de la temporada. Si se omite, se usa el ID raíz.')
        parser.add_argument('--file-index', type=int, choices=[1, 2, 3], required=True, help='Índice del archivo JSON.')
        parser.add_argument('--range', type=str, required=True, help='Rango de episodios. Formato: "5" o "5-10".')

    def parse_range(self, range_str):
        if '-' in range_str:
            start, end = map(int, range_str.split('-'))
            return list(range(start, end + 1))
        else:
            return [int(range_str)]

    def handle(self, *args, **kwargs):
        root_id = kwargs['root_anilist_id']
        season_id = kwargs['season_anilist_id'] if kwargs['season_anilist_id'] is not None else root_id
        file_index = kwargs['file_index']
        episodes_to_add = self.parse_range(kwargs['range'])
        target_file = get_data_file_path(file_index)
        local_data = load_local_data(target_file)
        
        anime_json = next((item for item in local_data.get('anime', []) if item.get('id') == root_id), None)
        
        if not anime_json:
            self.stdout.write(self.style.WARNING(f"No se encontró el anime con ID {root_id}. Se creará una nueva ficha."))
            anime_details = get_anime_details(root_id)
            if not anime_details:
                raise CommandError(f"No se pudo obtener información de AniList para el ID raíz {root_id}.")
            
            page_data = find_animeflv_page_data(anime_details)
            if page_data:
                details = scrape_animeflv_page_details(page_data['url'])
                if details['synopsis']:
                    anime_details['overview'] = details['synopsis']

            anime_json = build_base_anime_json(anime_details)
            local_data['anime'].append(anime_json)
        
        season_json = next((s for s in anime_json.get('seasons', []) if s.get('anilist_id') == season_id), None)
        if not season_json:
            next_season_number = len(anime_json.get('seasons', [])) + 1
            season_details = get_anime_details(season_id)
            season_title = season_details['title'] if season_details else "Temporada Desconocida"
            season_json = {'anilist_id': season_id, 'episodes': [], 'display_title': f'Temporada {next_season_number}', 'title': season_title, 'season_number': next_season_number}
            anime_json['seasons'].append(season_json)
        
        self.stdout.write(self.style.SUCCESS(f"Actualizando temporada '{season_json.get('display_title', season_json.get('title'))}' del anime '{anime_json['title']}'..."))

        season_details = get_anime_details(season_id)
        if not season_details:
            raise CommandError(f"No se pudo obtener información para la temporada con ID {season_id}")

        page_data = find_animeflv_page_data(season_details)
        if not page_data:
            raise CommandError("No se pudo encontrar la temporada en AnimeFLV.")
        
        page_details = scrape_animeflv_page_details(page_data['url'])
        all_available_episodes = page_details['episodes_list']
        episodes_to_process = [ep for ep in all_available_episodes if ep['number'] in episodes_to_add]
        
        if not episodes_to_process:
            self.stdout.write(self.style.WARNING(f"No se encontraron los episodios del rango solicitado en AnimeFLV."))
            return

        added_count = 0
        for ep_info in episodes_to_process:
            self.stdout.write(f"  -> Scrapeando episodio {ep_info['number']}...")
            sources = scrape_episode_sources(ep_info['url'])
            if sources:
                episode_json = { "episode_number": ep_info['number'], "title": f"Episodio {ep_info['number']}", "overview": "", "sources": sources }
                existing_ep_index = next((idx for idx, ep in enumerate(season_json['episodes']) if ep.get('episode_number') == ep_info['number']), -1)
                if existing_ep_index != -1: 
                    season_json['episodes'][existing_ep_index] = episode_json
                else: 
                    season_json['episodes'].append(episode_json)
                added_count += 1
        
        season_json['episodes'].sort(key=lambda ep: ep.get('episode_number', 0))
        save_local_data(local_data, target_file)
        self.stdout.write(self.style.SUCCESS(f"\n¡Éxito! Se añadieron/actualizaron {added_count} episodios."))