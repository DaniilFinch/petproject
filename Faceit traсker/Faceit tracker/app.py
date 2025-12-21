from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
import re
from datetime import datetime

load_dotenv()

app = Flask(__name__)

FACEIT_API_KEY = os.getenv('FACEIT_API_KEY', 'c60fb845-a4a7-4bda-beb6-1030a921424d')
FACEIT_API_URL = 'https://open.faceit.com/data/v4'
STEAM_API_KEY = os.getenv('STEAM_API_KEY', 'C6F00054110F3C76911BA7B211ABED47')

headers = {
    'Authorization': f'Bearer {FACEIT_API_KEY}',
    'accept': 'application/json'
}


def search_player_on_faceit(nickname, max_attempts=3):
    """Улучшенный поиск игрока на Faceit с несколькими попытками"""
    attempts = [
        # Попытка 1: точный поиск
        {'nickname': nickname, 'game': 'cs2'},
        # Попытка 2: без указания игры
        {'nickname': nickname},
        # Попытка 3: с похожим никнеймом (убираем спецсимволы)
        {'nickname': re.sub(r'[^a-zA-Z0-9]', '', nickname), 'game': 'cs2'},
    ]

    for i, params in enumerate(attempts[:max_attempts]):
        try:
            print(f"🔍 Попытка поиска {i + 1}: {params}")
            response = requests.get(
                f'{FACEIT_API_URL}/players',
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('player_id'):
                    print(f"✓ Найден игрок: {data.get('nickname')}")
                    return {
                        'player_id': data.get('player_id'),
                        'nickname': data.get('nickname'),
                        'found': True
                    }
            elif response.status_code == 404:
                print(f"✗ Игрок не найден (404)")
                continue
            else:
                print(f"⚠ Ошибка API: {response.status_code}")

        except Exception as e:
            print(f"⚠ Ошибка при попытке {i + 1}: {e}")
            continue

    # Если не нашли, пробуем поиск по всем игрокам с похожим никнеймом
    try:
        print(f"🔍 Пробуем расширенный поиск...")
        response = requests.get(
            f'{FACEIT_API_URL}/search/players',
            headers=headers,
            params={'nickname': nickname, 'game': 'cs2', 'limit': 10},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if items:
                # Берем первого наиболее релевантного игрока
                player = items[0]
                print(f"✓ Найден в расширенном поиске: {player.get('nickname')}")
                return {
                    'player_id': player.get('player_id'),
                    'nickname': player.get('nickname'),
                    'found': True
                }
    except Exception as e:
        print(f"⚠ Ошибка расширенного поиска: {e}")

    return {'found': False, 'error': 'Игрок не найден'}


def get_steam_id_from_faceit(player_id):
    """Получает Steam ID из профиля Faceit"""
    try:
        print(f"🔍 Получаем Steam ID для Faceit игрока {player_id}")

        # Получаем информацию об игроке с деталями
        response = requests.get(
            f'{FACEIT_API_URL}/players/{player_id}',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            player_data = response.json()

            # Ищем Steam ID в разных местах
            steam_id = None

            # 1. В поле steam_id_64
            if player_data.get('steam_id_64'):
                steam_id = player_data.get('steam_id_64')
                print(f"✓ Найден Steam ID в steam_id_64: {steam_id}")

            # 2. В поле steam_nickname
            elif player_data.get('steam_nickname'):
                steam_name = player_data.get('steam_nickname')
                print(f"✓ Найден Steam никнейм: {steam_name}")
                # Пробуем конвертировать в Steam ID
                steam_id = convert_steam_name_to_id(steam_name)

            # 3. В играх CS2
            elif player_data.get('games', {}).get('cs2', {}).get('game_player_id'):
                game_player_id = player_data['games']['cs2']['game_player_id']
                if re.match(r'^\d{17}$', game_player_id):
                    steam_id = game_player_id
                    print(f"✓ Найден Steam ID в game_player_id: {steam_id}")

            # 4. В общих платформах
            elif player_data.get('platforms', {}).get('steam'):
                steam_id = player_data['platforms']['steam']
                print(f"✓ Найден Steam ID в platforms: {steam_id}")

            if steam_id:
                # Проверяем, что это валидный Steam ID (17 цифр)
                if re.match(r'^\d{17}$', steam_id):
                    print(f"✅ Валидный Steam ID: {steam_id}")
                    return steam_id
                else:
                    print(f"⚠ Steam ID невалидный: {steam_id}")

            print("✗ Steam ID не найден в профиле Faceit")
            return None

    except Exception as e:
        print(f"⚠ Ошибка получения Steam ID: {e}")

    return None


def convert_steam_name_to_id(steam_name):
    """Конвертирует Steam никнейм в Steam ID через API"""
    if not STEAM_API_KEY:
        return None

    try:
        # Сначала пробуем получить Steam ID по никнейму
        response = requests.get(
            'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/',
            params={
                'key': STEAM_API_KEY,
                'vanityurl': steam_name
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('response', {}).get('success') == 1:
                steam_id = data['response']['steamid']
                print(f"✓ Конвертирован Steam никнейм в ID: {steam_id}")
                return steam_id
    except Exception as e:
        print(f"⚠ Ошибка конвертации Steam никнейма: {e}")

    return None


def get_steam_profile_info(steam_id):
    """Получает информацию о Steam профиле"""
    if not STEAM_API_KEY or not steam_id:
        return None

    try:
        response = requests.get(
            'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/',
            params={
                'key': STEAM_API_KEY,
                'steamids': steam_id
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            players = data.get('response', {}).get('players', [])
            if players:
                player = players[0]
                return {
                    'steamid': player.get('steamid'),
                    'personaname': player.get('personaname'),
                    'profileurl': player.get('profileurl'),
                    'avatar': player.get('avatar'),
                    'avatarmedium': player.get('avatarmedium'),
                    'avatarfull': player.get('avatarfull'),
                    'personastate': player.get('personastate')
                }
    except Exception as e:
        print(f"⚠ Ошибка получения Steam профиля: {e}")

    return None


def extract_steam_id_from_url(url):
    """Извлекает Steam ID из различных форматов ссылок Steam"""
    url = url.strip().lower()

    # Steam Community URL
    if 'steamcommunity.com' in url:
        # Формат: https://steamcommunity.com/profiles/76561197960287930
        match = re.search(r'steamcommunity\.com/profiles/(\d+)', url)
        if match:
            return match.group(1)

        # Формат: https://steamcommunity.com/id/username
        match = re.search(r'steamcommunity\.com/id/([^/]+)', url)
        if match:
            vanity_name = match.group(1)
            return convert_steam_name_to_id(vanity_name)

    # SteamID64 напрямую (17 цифр)
    if re.match(r'^\d{17}$', url):
        return url

    # Короткая ссылка: steam://friends/add/76561197960287930
    if 'steam://' in url:
        match = re.search(r'steam://friends/add/(\d+)', url)
        if match:
            return match.group(1)

    return None


def find_faceit_by_steam_id(steam_id):
    """Ищет Faceit профиль по Steam ID"""
    try:
        print(f"🔍 Ищем Faceit профиль по Steam ID: {steam_id}")

        # Пробуем найти через поиск Steam ID на Faceit
        response = requests.get(
            f'{FACEIT_API_URL}/players',
            headers=headers,
            params={'game_player_id': steam_id, 'game': 'cs2'},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('player_id'):
                print(f"✓ Найден Faceit профиль по Steam ID: {data.get('nickname')}")
                return data.get('nickname')

        # Если не нашли, пробуем получить никнейм Steam и искать по нему
        steam_name = get_steam_profile_info(steam_id)
        if steam_name and steam_name.get('personaname'):
            print(f"🔍 Ищем Faceit по Steam никнейму: {steam_name.get('personaname')}")
            search_result = search_player_on_faceit(steam_name.get('personaname'))
            if search_result['found']:
                return search_result['nickname']

    except Exception as e:
        print(f"⚠ Ошибка поиска Faceit по Steam ID: {e}")

    return None


def extract_nickname_from_url(url):
    """Извлекает никнейм из ссылки Faceit или Steam"""
    url = url.strip().rstrip('/')

    print(f"📥 Обработка ввода: {url}")

    # Если это Steam ссылка или Steam ID
    if 'steam' in url.lower() or re.match(r'^\d{17}$', url):
        steam_id = extract_steam_id_from_url(url)
        if steam_id:
            print(f"✓ Извлечен Steam ID: {steam_id}")
            faceit_nickname = find_faceit_by_steam_id(steam_id)
            if faceit_nickname:
                return faceit_nickname
            # Если не нашли Faceit, возвращаем Steam ID для поиска
            return steam_id

    # Если это Faceit ссылка
    if 'faceit.com' in url.lower():
        patterns = [
            r'faceit\.com/(?:[a-z]{2}/)?players?/([^/?]+)',
            r'/(?:players?/)?([^/?]+)$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                nickname = match.group(1)
                print(f"✓ Извлечен Faceit никнейм из URL: {nickname}")
                return nickname.split('?')[0]

    # Если это просто текст (никнейм)
    print(f"📛 Используем как никнейм: {url}")
    return url


def get_player_id(nickname):
    """Получает Faceit ID игрока"""
    print(f"🆔 Поиск Faceit ID для: {nickname}")

    # Сначала пробуем улучшенный поиск
    search_result = search_player_on_faceit(nickname)

    if search_result['found']:
        return search_result['player_id']

    # Если не нашли по никнейму, может быть это Steam ID?
    if re.match(r'^\d{17}$', nickname):
        print(f"🔍 Ввод похож на Steam ID, пробуем поиск...")
        faceit_nickname = find_faceit_by_steam_id(nickname)
        if faceit_nickname:
            print(f"🔍 Ищем по найденному Faceit никнейму: {faceit_nickname}")
            search_result = search_player_on_faceit(faceit_nickname)
            if search_result['found']:
                return search_result['player_id']

    print(f"✗ Не удалось найти игрока: {nickname}")
    return None


def get_player_stats(player_id):
    try:
        print(f"📊 Получение статистики для ID: {player_id}")

        # Получаем информацию об игроке
        player_response = requests.get(
            f'{FACEIT_API_URL}/players/{player_id}',
            headers=headers,
            timeout=10
        )

        if player_response.status_code != 200:
            print(f"✗ Ошибка получения информации об игроке: {player_response.status_code}")
            return None

        player_data = player_response.json()
        print(f"✓ Получена информация об игроке: {player_data.get('nickname')}")

        # Получаем Steam ID
        steam_id = get_steam_id_from_faceit(player_id)
        steam_info = None

        if steam_id:
            steam_info = get_steam_profile_info(steam_id)
            if steam_info:
                print(f"✓ Получена информация о Steam профиле: {steam_info.get('personaname')}")
            else:
                print("⚠ Не удалось получить Steam информацию (возможно, нет API ключа)")

        # Получаем статистику CS2 отдельно
        stats_response = requests.get(
            f'{FACEIT_API_URL}/players/{player_id}/stats/cs2',
            headers=headers,
            timeout=10
        )

        stats_data = {}
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print("✓ Получена общая статистика CS2")

        # Получаем последние матчи
        matches_response = requests.get(
            f'{FACEIT_API_URL}/players/{player_id}/games/cs2/stats',
            headers=headers,
            params={'offset': 0, 'limit': 30},
            timeout=10
        )

        matches_data = {}
        if matches_response.status_code == 200:
            matches_data = matches_response.json()
            match_count = len(matches_data.get('items', []))
            print(f"✓ Получено последних матчей: {match_count}")
        else:
            print(f"⚠ Ошибка получения матчей: {matches_response.status_code}")

        return {
            'player': player_data,
            'steam_info': steam_info,
            'stats': stats_data,
            'matches': matches_data
        }
    except Exception as e:
        print(f"✗ Ошибка получения статистики: {e}")
        return None


def calculate_recent_stats(matches, player_id):
    """ПРАВИЛЬНЫЙ расчет статистики на основе реальной структуры данных"""
    if not matches or 'items' not in matches:
        print("Нет данных о матчах")
        return {
            'total_matches': 0,
            'wins': 0,
            'losses': 0,
            'total_kills': 0,
            'total_deaths': 0,
            'total_assists': 0,
            'kd_ratio': 0,
            'win_rate': 0,
            'avg_kills': 0,
            'avg_deaths': 0,
            'avg_assists': 0
        }

    items = matches['items']
    print(f"🔍 Анализируем {len(items)} матчей")

    total_kills = 0
    total_deaths = 0
    total_assists = 0
    total_matches = len(items)
    wins = 0

    for i, match in enumerate(items):
        # Получаем статистику из match['stats']
        stats = match.get('stats', {})

        # Получаем K/D/A
        kills = int(stats.get('Kills', 0) or 0)
        deaths = int(stats.get('Deaths', 0) or 0)
        assists = int(stats.get('Assists', 0) or 0)

        total_kills += kills
        total_deaths += deaths
        total_assists += assists

        # Определяем победу
        result = stats.get('Result', '0')
        if str(result) == '1':
            wins += 1

    print(f"\n📈 ИТОГО:")
    print(f"  Матчи: {total_matches}")
    print(f"  Побед: {wins}")
    print(f"  Поражений: {total_matches - wins}")

    # Рассчитываем показатели
    kd_ratio = round(total_kills / max(total_deaths, 1), 2)
    win_rate = round((wins / max(total_matches, 1)) * 100) if total_matches > 0 else 0
    avg_kills = round(total_kills / max(total_matches, 1), 1)
    avg_deaths = round(total_deaths / max(total_matches, 1), 1)
    avg_assists = round(total_assists / max(total_matches, 1), 1)

    return {
        'total_matches': total_matches,
        'wins': wins,
        'losses': total_matches - wins,
        'total_kills': total_kills,
        'total_deaths': total_deaths,
        'total_assists': total_assists,
        'kd_ratio': kd_ratio,
        'win_rate': win_rate,
        'avg_kills': avg_kills,
        'avg_deaths': avg_deaths,
        'avg_assists': avg_assists
    }


def prepare_matches_data(matches, player_id):
    if not matches or 'items' not in matches:
        return []

    prepared_matches = []

    for match in matches['items']:
        stats = match.get('stats', {})

        match_id = stats.get('Match Id', '')
        map_name = stats.get('Map', 'Unknown')

        # Время окончания матча
        finished_at = match.get('finished_at', '')
        if not finished_at and 'Match Finished At' in stats:
            try:
                timestamp = stats['Match Finished At'] / 1000
                finished_at = datetime.fromtimestamp(timestamp).isoformat() + 'Z'
            except:
                finished_at = ''

        # Получаем K/D/A
        kills = int(stats.get('Kills', 0) or 0)
        deaths = int(stats.get('Deaths', 0) or 0)
        assists = int(stats.get('Assists', 0) or 0)

        # Определяем результат
        result = 'loss'
        match_result = stats.get('Result', '0')
        if str(match_result) == '1':
            result = 'win'

        prepared_matches.append({
            'match_id': match_id,
            'map': map_name,
            'date': finished_at,
            'kills': kills,
            'deaths': deaths,
            'assists': assists,
            'result': result
        })

    return prepared_matches


def get_total_matches(player_info, stats_data):
    """Получаем общее количество матчей из разных источников"""
    # Способ 1: из информации об игроке
    cs2_stats = player_info.get('games', {}).get('cs2', {})
    total_matches = cs2_stats.get('total_matches', 0)

    # Способ 2: из статистики
    if total_matches == 0 and stats_data and 'lifetime' in stats_data:
        lifetime = stats_data.get('lifetime', {})
        total_matches = lifetime.get('Matches', 0)

    return total_matches


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_stats', methods=['POST'])
def get_stats():
    try:
        input_data = request.json.get('input', '').strip()

        print(f"\n{'=' * 60}")
        print(f"🎮 FACEIT TRACKER - ПОИСК ИГРОКА")
        print(f"{'=' * 60}")
        print(f"📥 Ввод: {input_data}")

        if not input_data:
            return jsonify({'error': 'Введите никнейм, ссылку на Faceit или Steam профиль'}), 400

        # Извлекаем никнейм (поддерживает Faceit, Steam ссылки и Steam ID)
        nickname = extract_nickname_from_url(input_data)

        print(f"📛 Извлеченный идентификатор: {nickname}")

        if not nickname:
            return jsonify({'error': 'Не удалось извлечь идентификатор игрока'}), 400

        # Получаем ID игрока на Faceit
        player_id = get_player_id(nickname)

        if not player_id:
            error_msg = f'Игрок "{nickname}" не найден на Faceit.'
            error_msg += '\nВозможные причины:'
            error_msg += '\n• Игрок не играет в CS2 на Faceit'
            error_msg += '\n• Никнейм указан неправильно'
            error_msg += '\n• Используйте ссылку на Steam профиль'
            return jsonify({'error': error_msg}), 404

        print(f"🆔 Faceit Player ID: {player_id}")

        # Получаем статистику
        stats_data = get_player_stats(player_id)

        if not stats_data:
            return jsonify({'error': 'Не удалось получить статистику с Faceit'}), 500

        # Рассчитываем статистику
        recent_stats = calculate_recent_stats(stats_data['matches'], player_id)

        # Подготавливаем данные матчей
        prepared_matches = prepare_matches_data(stats_data['matches'], player_id)

        # Получаем общую информацию
        player_info = stats_data['player']
        cs2_stats = player_info.get('games', {}).get('cs2', {})

        # Получаем общее количество матчей
        total_all_matches = get_total_matches(player_info, stats_data.get('stats', {}))

        # Формируем ответ с Steam информацией
        result = {
            'success': True,
            'nickname': player_info.get('nickname', nickname),
            'player_info': {
                'player_id': player_id,
                'avatar': player_info.get('avatar', ''),
                'country': player_info.get('country', ''),
                'skill_level': cs2_stats.get('skill_level', 'N/A'),
                'faceit_elo': cs2_stats.get('faceit_elo', 'N/A'),
                'total_matches': total_all_matches
            },
            'steam_info': stats_data.get('steam_info'),
            'recent_stats': recent_stats,
            'matches': prepared_matches
        }

        print(f"\n✅ РЕЗУЛЬТАТ ПОИСКА:")
        print(f"   Игрок: {result['nickname']}")
        print(f"   Уровень: {result['player_info']['skill_level']}")
        print(f"   ELO: {result['player_info']['faceit_elo']}")
        print(f"   Всего матчей: {total_all_matches}")
        print(f"   Последние матчи: {recent_stats['total_matches']}")
        print(f"   Побед: {recent_stats['wins']} ({recent_stats['win_rate']}%)")
        print(f"   K/D: {recent_stats['kd_ratio']}")
        if result['steam_info']:
            print(f"   Steam: {result['steam_info'].get('personaname')}")
        print(f"{'=' * 60}\n")

        return jsonify(result)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)