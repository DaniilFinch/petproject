# faceit_backup.py - Альтернативные источники данных
import requests
import json
import time
from bs4 import BeautifulSoup


class FaceitBackup:
    """Резервные методы получения данных, если API не работает"""

    @staticmethod
    def search_via_web(nickname):
        """Поиск через веб-страницу FACEIT (резервный метод)"""
        try:
            url = f"https://www.faceit.com/players/{nickname}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Пытаемся извлечь данные со страницы
                player_data = {
                    'nickname': nickname,
                    'source': 'web_scrape',
                    'url': url
                }

                # Ищем мета-теги
                meta_tags = soup.find_all('meta')
                for tag in meta_tags:
                    if tag.get('property') == 'og:title':
                        player_data['title'] = tag.get('content', '')

                    if tag.get('property') == 'og:image':
                        player_data['avatar'] = tag.get('content', '')

                # Ищем информацию на странице
                stats_div = soup.find('div', class_='player-profile-header')
                if stats_div:
                    player_data['raw_html'] = str(stats_div)[:500]

                return player_data

        except Exception as e:
            print(f"⚠️ Веб-поиск не удался: {e}")

        return None

    @staticmethod
    def get_known_players():
        """База известных игроков для демо"""
        return {
            's1mple': {
                'player_id': '1-2b123456-1234-1234-1234-123456789012',
                'nickname': 's1mple',
                'country': 'UA',
                'avatar': 'https://cdn.faceit.com/avatars/1a2b3c4d-1234-5678-9abc-def012345678_152.jpg',
                'skill_level': 10,
                'faceit_elo': 3472,
                'game': 'cs2'
            },
            'niko': {
                'player_id': '2-3c234567-2345-2345-2345-234567890123',
                'nickname': 'NiKo',
                'country': 'BA',
                'avatar': 'https://cdn.faceit.com/avatars/2b3c4d5e-2345-6789-0bcd-ef1234567890_152.jpg',
                'skill_level': 10,
                'faceit_elo': 3124,
                'game': 'cs2'
            },
            'zywoo': {
                'player_id': '3-4d345678-3456-3456-3456-345678901234',
                'nickname': 'ZywOo',
                'country': 'FR',
                'avatar': 'https://cdn.faceit.com/avatars/3c4d5e6f-3456-7890-1cde-f23456789012_152.jpg',
                'skill_level': 10,
                'faceit_elo': 3415,
                'game': 'cs2'
            },
            'dev1ce': {
                'player_id': '4-5e456789-4567-4567-4567-456789012345',
                'nickname': 'dev1ce',
                'country': 'DK',
                'avatar': 'https://cdn.faceit.com/avatars/4d5e6f7g-4567-8901-2def-g34567890123_152.jpg',
                'skill_level': 10,
                'faceit_elo': 3289,
                'game': 'cs2'
            },
            'm0nesy': {
                'player_id': '5-6f567890-5678-5678-5678-567890123456',
                'nickname': 'm0NESY',
                'country': 'RU',
                'avatar': 'https://cdn.faceit.com/avatars/5e6f7g8h-5678-9012-3efg-h45678901234_152.jpg',
                'skill_level': 10,
                'faceit_elo': 3350,
                'game': 'cs2'
            }
        }

    @staticmethod
    def search_in_database(nickname):
        """Поиск в локальной базе известных игроков"""
        players = FaceitBackup.get_known_players()
        nickname_lower = nickname.lower()

        # Точное совпадение
        if nickname_lower in players:
            return players[nickname_lower]

        # Частичное совпадение
        for key, player in players.items():
            if nickname_lower in key or key in nickname_lower:
                return player

        return None