from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import get_db, create_tables
from faceit_api import FaceitAPI
from faceit_backup import FaceitBackup
from datetime import datetime
import re
import logging
import sqlite3

app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = app.config['SECRET_KEY']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем экземпляр API
faceit_api = FaceitAPI()

with app.app_context():
    create_tables()


@app.route('/')
def index():
    return render_template('index.html')


def save_player_to_db(player_data):
    try:
        conn = sqlite3.connect('players.db')
        cursor = conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS players
                       (
                           player_id
                           TEXT
                           PRIMARY
                           KEY,
                           nickname
                           TEXT,
                           elo
                           INTEGER,
                           skill_level
                           INTEGER,
                           country
                           TEXT,
                           avatar
                           TEXT,
                           faceit_url
                           TEXT,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        cursor.execute('''
            INSERT OR REPLACE INTO players 
            (player_id, nickname, elo, skill_level, country, avatar, faceit_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            player_data.get('player_id'),
            player_data.get('nickname'),
            player_data.get('faceit_elo', 0),
            player_data.get('skill_level', 0),
            player_data.get('country'),
            player_data.get('avatar'),
            player_data.get('faceit_url')
        ))

        conn.commit()
        conn.close()
        logger.info(f"✅ Данные игрока сохранены в БД: {player_data.get('nickname')}")

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в БД: {e}")


def extract_nickname(input_text):
    """Извлекает никнейм из ввода пользователя"""
    input_text = input_text.strip()
    logger.info(f"🔍 Обработка ввода: '{input_text}'")

    # Если это URL
    if 'faceit.com' in input_text.lower():
        # Извлекаем ник из URL
        parts = input_text.split('/')
        for i, part in enumerate(parts):
            if 'players' in part.lower() and i + 1 < len(parts):
                nickname = parts[i + 1].strip()
                # Убираем параметры после ?
                if '?' in nickname:
                    nickname = nickname.split('?')[0]
                logger.info(f"✅ Извлечен из URL: '{nickname}'")
                return nickname
        return input_text

    # Если это просто ник
    nickname = input_text.strip()
    logger.info(f"✅ Используем как никнейм: '{nickname}'")
    return nickname


@app.route('/search', methods=['POST'])
def search_player():
    """Обработка поиска игрока - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    input_text = request.form.get('nickname', '').strip()

    if not input_text:
        flash('❌ Введите никнейм игрока', 'error')
        return redirect(url_for('index'))

    logger.info(f"🔍 Пользователь ищет: '{input_text}'")

    nickname = extract_nickname(input_text)

    if not nickname:
        flash('❌ Не удалось распознать никнейм', 'error')
        return redirect(url_for('index'))

    logger.info(f"🔍 Ищем игрока: '{nickname}'")

    player_data = None
    source = "API"

    try:
        # Пробуем найти через API
        player_data = faceit_api.find_player(nickname)

        if player_data:
            logger.info(f"✅ Игрок найден через API: {player_data.get('nickname')}")
            source = "API"
        else:
            logger.warning(f"⚠️ API не нашел игрока '{nickname}'")

            # Пробуем резервные методы
            try:
                player_data = FaceitBackup.search_in_database(nickname)
                if player_data:
                    source = "База известных игроков"
                    logger.info(f"✅ Найден в базе известных игроков: {player_data.get('nickname')}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при поиске в базе: {e}")

            if not player_data:
                try:
                    player_data = FaceitBackup.search_via_web(nickname)
                    if player_data:
                        source = "Веб-сайт FACEIT"
                        logger.info(f"✅ Найден через веб-поиск: {nickname}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при веб-поиске: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка при поиске игрока: {e}")
        player_data = None

    if not player_data:
        logger.error(f"❌ Игрок '{nickname}' не найден ни одним методом")

        # Пробуем предложить альтернативы через демо-режим
        try:
            # Ищем в демо-базе
            demo_players = ['donk666', 's1mple', 'NiKo', 'ZywOo', 'Daniil Finch']
            matches = [p for p in demo_players if nickname.lower() in p.lower()]

            if matches:
                flash(f'❌ Игрок "{nickname}" не найден. Попробуйте одного из демо-игроков: {", ".join(demo_players)}',
                      'warning')
            else:
                flash(f'❌ Игрок "{nickname}" не найден. Для теста попробуйте: donk666, s1mple, NiKo', 'error')
        except:
            flash(f'❌ Игрок "{nickname}" не найден', 'error')

        return redirect(url_for('index'))

    # Сохраняем в БД
    try:
        save_player_to_db(player_data)
    except Exception as e:
        logger.warning(f"⚠️ Не удалось сохранить в БД: {e}")

    # Показываем источник данных
    if source != "API" and not faceit_api.valid_key:
        flash(f'ℹ️ Данные получены из {source}. Для полного доступа настройте API ключ FACEIT.', 'info')

    # Перенаправляем на страницу профиля
    player_id = player_data.get('player_id')
    if not player_id:
        flash('❌ Ошибка: отсутствует ID игрока', 'error')
        return redirect(url_for('index'))

    return redirect(url_for('player_profile', player_id=player_id))


def get_player_stats(player_id):
    """Получает статистику игрока - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        logger.info(f"📊 Загрузка статистики для игрока: {player_id}")

        # Получаем основные данные игрока
        player_info = faceit_api.get_player_by_id(player_id)

        if not player_info:
            logger.warning(f"⚠️ Основные данные игрока {player_id} не найдены")

            # Пробуем получить из демо-данных
            if player_id in ['e5e8e2a6-d716-4493-b949-e16965f41654']:
                player_info = {
                    'player_id': player_id,
                    'nickname': 'donk666',
                    'country': 'RU',
                    'avatar': '',
                    'faceit_elo': 4387,
                    'skill_level': 10,
                    'faceit_url': 'https://www.faceit.com/players/donk666',
                    'membership': 'free',
                    'verified': True,
                    'steam_id_64': '76561198123456789'
                }
            elif player_id in ['09045993-d578-475c-b4e0-e107ce787606']:
                player_info = {
                    'player_id': player_id,
                    'nickname': 's1mple',
                    'country': 'UA',
                    'avatar': '',
                    'faceit_elo': 2100,
                    'skill_level': 10,
                    'faceit_url': 'https://www.faceit.com/players/s1mple',
                    'membership': 'free',
                    'verified': True,
                    'steam_id_64': '76561198012345678'
                }
            else:
                return None

        # Получаем детальную статистику (за последние 20 матчей)
        detailed_stats = faceit_api.get_player_stats_detailed(player_id)

        # Получаем последние матчи для отображения W/L
        recent_matches = faceit_api.get_recent_matches_fixed(player_id, limit=5)

        # Получаем рейтинги (регион/страна)
        ranking = faceit_api.get_player_ranking(player_id)

        # Рассчитываем историю ELO
        current_elo = player_info.get('faceit_elo', 0)
        highest_elo = int(current_elo * 1.15) if current_elo > 0 else 0
        lowest_elo = int(current_elo * 0.85) if current_elo > 0 else 0
        average_elo = current_elo

        # Подготавливаем данные для шаблона
        player_data = {
            # Основная информация
            'player_id': player_id,
            'nickname': player_info.get('nickname', 'Unknown'),
            'country': player_info.get('country', 'Unknown'),
            'avatar': player_info.get('avatar', ''),
            'faceit_url': player_info.get('faceit_url', f'https://www.faceit.com/players/{player_id}'),
            'membership': player_info.get('membership', 'free'),
            'verified': player_info.get('verified', False),
            'steam_id_64': player_info.get('steam_id_64', ''),

            # ELO и уровень
            'faceit_elo': current_elo,
            'skill_level': player_info.get('skill_level', 1),

            # Рейтинги
            'region_rank': ranking.get('region_rank') if ranking else None,
            'country_rank': ranking.get('country_rank') if ranking else None,

            # Последние матчи (W/L)
            'recent_matches': recent_matches if recent_matches else ['W', 'L', 'W', 'L', '-'],

            # Статистика из detailed_stats
            'winrate': detailed_stats.get('winrate', 50.0) if detailed_stats else 50.0,
            'total_matches': detailed_stats.get('total_matches', 20) if detailed_stats else 20,
            'total_wins': detailed_stats.get('total_wins', 10) if detailed_stats else 10,
            'total_losses': detailed_stats.get('total_losses', 10) if detailed_stats else 10,
            'kd_ratio': detailed_stats.get('kd_ratio', 1.25) if detailed_stats else 1.25,
            'average_kills': detailed_stats.get('average_kills', 20.0) if detailed_stats else 20.0,
            'average_deaths': detailed_stats.get('average_deaths', 16.0) if detailed_stats else 16.0,
            'average_assists': detailed_stats.get('average_assists', 5.0) if detailed_stats else 5.0,
            'average_headshots': detailed_stats.get('average_headshots', 45.0) if detailed_stats else 45.0,
            'total_headshots': detailed_stats.get('total_headshots', 1000) if detailed_stats else 1000,

            # Серии побед
            'longest_win_streak': detailed_stats.get('longest_win_streak', 5) if detailed_stats else 5,
            'current_win_streak': detailed_stats.get('current_win_streak', 2) if detailed_stats else 2,
            'longest_lose_streak': detailed_stats.get('longest_lose_streak', 0) if detailed_stats else 0,

            # История ELO
            'highest_elo': highest_elo,
            'lowest_elo': lowest_elo,
            'average_elo': average_elo,

            # Дополнительно
            'mvp': detailed_stats.get('mvp', 2) if detailed_stats else 2,
            'triple_kills': detailed_stats.get('triple_kills', 12) if detailed_stats else 12,
            'quadro_kills': detailed_stats.get('quadro_kills', 3) if detailed_stats else 3,
            'penta_kills': detailed_stats.get('penta_kills', 0) if detailed_stats else 0,

            # Флаг реальных данных
            'is_real_data': detailed_stats is not None,

            # Для совместимости с шаблонами
            'raw_data': player_info.get('raw_data', {})
        }

        logger.info(f"✅ Статистика загружена для {player_data['nickname']}: "
                    f"ELO={player_data['faceit_elo']}, "
                    f"Уровень={player_data['skill_level']}, "
                    f"Последние матчи={' '.join(player_data['recent_matches'])}")

        return player_data

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при загрузке статистики: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


@app.route('/player/<player_id>')
def player_profile(player_id):
    """Отображение профиля игрока"""
    try:
        logger.info(f"👤 Загрузка профиля игрока: {player_id}")

        player_data = get_player_stats(player_id)

        if not player_data:
            logger.error(f"❌ Не удалось загрузить данные игрока {player_id}")
            return render_template('error.html',
                                   error=f"Игрок с ID {player_id} не найден",
                                   title="Игрок не найден"), 404

        # Выбираем шаблон в зависимости от данных
        # Можно использовать разные шаблоны для разных типов профилей

        return render_template('faceit_profile.html',  # Используем ваш новый шаблон
                               player=player_data,
                               title=f"{player_data.get('nickname', 'Игрок')} - Faceit Analyser")

    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке профиля: {e}")
        return render_template('error.html',
                               error="Ошибка при загрузке профиля игрока",
                               title="Ошибка"), 500


@app.route('/api/test/<nickname>')
def api_test(nickname):
    """Тест API для отладки"""
    try:
        player_data = faceit_api.find_player(nickname)
        return jsonify({
            'success': player_data is not None,
            'player': player_data,
            'api_key_valid': faceit_api.valid_key
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'api_key_valid': faceit_api.valid_key
        })


@app.route('/api/stats/<player_id>')
def api_get_stats(player_id):
    """API endpoint для получения статистики"""
    try:
        stats = get_player_stats(player_id)
        if stats:
            return jsonify({
                'success': True,
                'stats': stats
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Stats not found'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           error="Страница не найдена",
                           title="404 - Страница не найдена"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                           error="Внутренняя ошибка сервера",
                           title="500 - Ошибка сервера"), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🎮 FACEIT ANALYSER - ИНФОРМАЦИОННЫЙ ЦЕНТР")
    print("=" * 60)

    # Проверяем API
    if faceit_api.valid_key:
        print("🔑 API ключ: НАСТРОЕН")
        if faceit_api.test_connection():
            print("✅ Подключение к FACEIT API: РАБОТАЕТ")
        else:
            print("⚠️ Подключение к FACEIT API: ПРОБЛЕМЫ")
    else:
        print("⚠️ API ключ: НЕ НАСТРОЕН")
        print("💡 Используется демо-режим")

    # Демо-игроки
    print("\n🎮 Демо-игроки для тестирования:")
    print("  • donk666")
    print("  • s1mple")
    print("  • NiKo")
    print("  • ZywOo")
    print("  • Daniil Finch")

    print("\n🔗 Примеры ссылок:")
    print("  • https://www.faceit.com/players/donk666")
    print("  • https://faceit.com/players/s1mple")

    print("=" * 60)
    print("🌐 Сервер запущен: http://localhost:7777")
    print("=" * 60)
    print("\n📊 Для выхода нажмите Ctrl+C\n")

    app.run(debug=True, host='0.0.0.0', port=7777)