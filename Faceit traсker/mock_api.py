# mock_api.py
import uuid
from datetime import datetime, timedelta
import random


def get_mock_player(nickname):
    """Возвращает mock-данные игрока"""
    # Преобразуем никнейм к нижнему регистру для сравнения
    nickname_lower = nickname.lower()

    # База популярных игроков
    popular_players = {
        's1mple': {
            'player_id': '1a2b3c4d-1234-5678-9abc-def012345678',
            'nickname': 's1mple',
            'country': 'UA',
            'avatar': 'https://cdn.faceit.com/avatars/1a2b3c4d-1234-5678-9abc-def012345678_152.jpg',
            'skill_level': 10,
            'faceit_elo': 3500,
            'game': 'cs2'
        },
        'niko': {
            'player_id': '2b3c4d5e-2345-6789-0bcd-ef1234567890',
            'nickname': 'NiKo',
            'country': 'BA',
            'avatar': 'https://cdn.faceit.com/avatars/2b3c4d5e-2345-6789-0bcd-ef1234567890_152.jpg',
            'skill_level': 10,
            'faceit_elo': 3200,
            'game': 'cs2'
        },
        'zywoo': {
            'player_id': '3c4d5e6f-3456-7890-1cde-f23456789012',
            'nickname': 'ZywOo',
            'country': 'FR',
            'avatar': 'https://cdn.faceit.com/avatars/3c4d5e6f-3456-7890-1cde-f23456789012_152.jpg',
            'skill_level': 10,
            'faceit_elo': 3400,
            'game': 'cs2'
        },
        'device': {
            'player_id': '4d5e6f7g-4567-8901-2def-g34567890123',
            'nickname': 'dev1ce',
            'country': 'DK',
            'avatar': 'https://cdn.faceit.com/avatars/4d5e6f7g-4567-8901-2def-g34567890123_152.jpg',
            'skill_level': 10,
            'faceit_elo': 3300,
            'game': 'cs2'
        },
        'rain': {
            'player_id': '5e6f7g8h-5678-9012-3efg-h45678901234',
            'nickname': 'rain',
            'country': 'NO',
            'avatar': 'https://cdn.faceit.com/avatars/5e6f7g8h-5678-9012-3efg-h45678901234_152.jpg',
            'skill_level': 9,
            'faceit_elo': 2800,
            'game': 'cs2'
        },
        'twistzz': {
            'player_id': '6f7g8h9i-6789-0123-4fgh-i56789012345',
            'nickname': 'Twistzz',
            'country': 'CA',
            'avatar': 'https://cdn.faceit.com/avatars/6f7g8h9i-6789-0123-4fgh-i56789012345_152.jpg',
            'skill_level': 9,
            'faceit_elo': 2900,
            'game': 'cs2'
        }
    }

    # Проверяем точное совпадение
    if nickname_lower in popular_players:
        return popular_players[nickname_lower]

    # Проверяем частичное совпадение
    for key, player in popular_players.items():
        if key in nickname_lower or nickname_lower in key:
            return player

    # Создаем нового случайного игрока
    countries = ['RU', 'UA', 'BY', 'KZ', 'PL', 'DE', 'FR', 'UK', 'US', 'BR']
    country = random.choice(countries)

    # Генерируем случайный уровень и ELO
    skill_level = random.randint(1, 10)
    faceit_elo = 1000 + (skill_level * 200) + random.randint(-100, 100)

    return {
        'player_id': str(uuid.uuid4()),
        'nickname': nickname[:20],  # Ограничиваем длину
        'country': country,
        'avatar': f'https://cdn.faceit.com/avatars/{str(uuid.uuid4())}_152.jpg',
        'skill_level': skill_level,
        'faceit_elo': faceit_elo,
        'game': 'cs2'
    }


def get_mock_matches(player_id, count=5):
    """Возвращает mock-матчи"""
    matches = []
    maps = ['Mirage', 'Inferno', 'Dust2', 'Nuke', 'Vertigo', 'Overpass', 'Ancient']

    for i in range(count):
        match_date = datetime.now() - timedelta(days=i * 2)
        is_win = random.random() > 0.5  # 50% шанс на победу

        # Генерируем реалистичную статистику
        kills = random.randint(10, 35)
        deaths = random.randint(8, 30)
        kd_ratio = round(kills / max(deaths, 1), 2)
        hs_percent = round(random.uniform(20.0, 70.0), 1)

        matches.append({
            'match_id': f'mock_match_{i}_{player_id}',
            'player_id': player_id,
            'result': 'win' if is_win else 'loss',
            'kills': kills,
            'deaths': deaths,
            'kd_ratio': kd_ratio,
            'hs_percent': hs_percent,
            'map_name': random.choice(maps),
            'date': match_date.strftime('%Y-%m-%d %H:%M:%S')
        })

    return matches


class MockFaceitAPI:
    """Mock API для тестирования"""

    def __init__(self):
        print("🔄 Using Mock API (no real API calls)")

    def search_player_by_nickname(self, nickname):
        print(f"🔍 [MOCK] Searching player: {nickname}")
        player = get_mock_player(nickname)

        # Добавляем небольшую задержку для реалистичности
        import time
        time.sleep(0.5)

        return player

    def get_player_by_id(self, player_id):
        print(f"📋 [MOCK] Getting player by ID: {player_id}")

        # Для mock API создаем игрока с указанным ID
        return {
            'player_id': player_id,
            'nickname': f'Player_{player_id[:8]}',
            'country': 'RU',
            'avatar': f'https://cdn.faceit.com/avatars/{player_id}_152.jpg',
            'skill_level': random.randint(1, 10),
            'faceit_elo': random.randint(1000, 3500),
            'game': 'cs2'
        }

    def get_player_matches(self, player_id, limit=5):
        print(f"🎮 [MOCK] Getting matches for: {player_id}")

        matches = get_mock_matches(player_id, limit)

        # Добавляем структуру, ожидаемую приложением
        processed_matches = []
        for match in matches:
            processed_matches.append({
                'match_id': match['match_id'],
                'result': match['result'],
                'stats': {
                    'kills': match['kills'],
                    'deaths': match['deaths'],
                    'kd_ratio': match['kd_ratio'],
                    'hs_percent': match['hs_percent']
                },
                'map_name': match['map_name'],
                'date': match['date']
            })

        return processed_matches

    def test_connection(self):
        print("✅ [MOCK] API connection test successful")
        return True


# Экспортируем функции для использования в других модулях
__all__ = ['get_mock_player', 'get_mock_matches', 'MockFaceitAPI']