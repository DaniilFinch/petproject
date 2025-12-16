# diagnose_faceit.py
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


class FaceitDiagnoser:
    def __init__(self):
        self.api_key = os.getenv('FACEIT_API_KEY', '')
        self.base_url = 'https://open.faceit.com/data/v4'
        self.headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}

    def test_all_endpoints(self, nickname="s1mple"):
        """Тестируем ВСЕ возможные endpoint'ы"""
        print("🔍" * 30)
        print("FACEIT API ДИАГНОСТИКА")
        print("🔍" * 30)

        if not self.api_key:
            print("❌ API ключ не найден в .env файле!")
            print("💡 Создайте .env файл с FACEIT_API_KEY=ваш_ключ")
            return False

        print(f"🔑 API Key: {self.api_key[:10]}...")
        print(f"🎯 Тестируемый никнейм: {nickname}")
        print("-" * 60)

        tests = [
            ("Общая проверка API", "/games", None),
            ("Поиск игрока (новый)", "/players", {'nickname': nickname, 'limit': 20}),
            ("Поиск игрока (старый)", "/search/players", {'nickname': nickname, 'game': 'cs2', 'limit': 1}),
            ("Игры FACEIT", "/games/cs2", None),
            ("Чемпионаты", "/championships", {'game': 'cs2', 'type': 'all', 'offset': 0, 'limit': 1}),
        ]

        results = []

        for test_name, endpoint, params in tests:
            print(f"\n🧪 {test_name}")
            print(f"📡 Endpoint: {endpoint}")

            url = self.base_url + endpoint
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)

                print(f"📊 Status: {response.status_code}")
                print(f"⏱️  Response time: {response.elapsed.total_seconds():.2f}s")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ УСПЕХ!")

                    if 'items' in data:
                        items = data['items']
                        print(f"📦 Найдено записей: {len(items)}")

                        if items and 'nickname' in items[0]:
                            players_found = [item['nickname'] for item in items[:3]]
                            print(f"👤 Игроки: {', '.join(players_found)}")

                    elif 'player_id' in data:
                        print(f"👤 Игрок: {data.get('nickname')} (ID: {data.get('player_id')})")

                    results.append((test_name, True, data))
                else:
                    print(f"❌ ОШИБКА: {response.text[:200]}")
                    results.append((test_name, False, response.text))

            except Exception as e:
                print(f"💥 ИСКЛЮЧЕНИЕ: {e}")
                results.append((test_name, False, str(e)))

        print("\n" + "=" * 60)
        print("📋 ИТОГИ ДИАГНОСТИКИ:")
        print("=" * 60)

        for test_name, success, data in results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}")

        return any(success for _, success, _ in results)

    def find_player_any_method(self, nickname):
        """Ищем игрока ВСЕМИ возможными методами"""
        print(f"\n🎯 ПОИСК ИГРОКА '{nickname}' ВСЕМИ СПОСОБАМИ:")

        methods = [
            ("Прямой поиск /players", f"/players?nickname={nickname}&limit=20"),
            ("Поиск через /search", f"/search/players?nickname={nickname}&game=cs2&limit=10"),
            ("Поиск без игры", f"/players?nickname={nickname}&limit=10"),
        ]

        found_players = []

        for method_name, endpoint in methods:
            print(f"\n🔍 {method_name}")
            url = self.base_url + endpoint

            try:
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    if 'items' in data and data['items']:
                        for player in data['items']:
                            player_info = {
                                'method': method_name,
                                'nickname': player.get('nickname'),
                                'player_id': player.get('player_id'),
                                'country': player.get('country'),
                                'similarity': self.calculate_similarity(nickname, player.get('nickname', ''))
                            }
                            found_players.append(player_info)

                            print(f"   👤 {player.get('nickname')} "
                                  f"(ID: {player.get('player_id')}, "
                                  f"Сходство: {player_info['similarity']}%)")

                    elif 'player_id' in data:
                        player_info = {
                            'method': method_name,
                            'nickname': data.get('nickname'),
                            'player_id': data.get('player_id'),
                            'similarity': 100
                        }
                        found_players.append(player_info)
                        print(f"   👤 {data.get('nickname')} (прямой результат)")

            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

        # Фильтруем и сортируем
        if found_players:
            print(f"\n🎯 НАЙДЕНО {len(found_players)} ИГРОКОВ:")

            # Сортируем по сходству
            found_players.sort(key=lambda x: x['similarity'], reverse=True)

            for i, player in enumerate(found_players[:5], 1):
                print(f"{i}. {player['nickname']} "
                      f"(сходство: {player['similarity']}%, "
                      f"метод: {player['method']})")

            return found_players[0] if found_players[0]['similarity'] > 70 else None

        return None

    def calculate_similarity(self, str1, str2):
        """Вычисляет процент сходства строк"""
        str1_lower = str1.lower()
        str2_lower = str2.lower()

        if str1_lower == str2_lower:
            return 100

        # Простой алгоритм сходства
        set1 = set(str1_lower)
        set2 = set(str2_lower)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return int((intersection / union) * 100) if union > 0 else 0

    def check_api_limits(self):
        """Проверяем лимиты API"""
        print("\n📊 ПРОВЕРКА ЛИМИТОВ API:")

        # Заголовки ответа содержат информацию о лимитах
        url = self.base_url + "/games"

        try:
            response = requests.get(url, headers=self.headers, timeout=5)

            limits = {
                'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit', 'Unknown'),
                'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining', 'Unknown'),
                'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset', 'Unknown')
            }

            print(f"🔄 Лимит запросов: {limits['X-RateLimit-Limit']}")
            print(f"📉 Осталось запросов: {limits['X-RateLimit-Remaining']}")
            print(f"🕐 Сброс через: {limits['X-RateLimit-Reset']} секунд")

        except Exception as e:
            print(f"❌ Не удалось проверить лимиты: {e}")


if __name__ == '__main__':
    diagnoser = FaceitDiagnoser()

    # Тестируем с разными никнеймами
    test_nicknames = ["s1mple", "NiKo", "ZywOo", "dev1ce", "m0NESY", "test12345"]

    for nickname in test_nicknames:
        print("\n" + "=" * 60)
        print(f"🎯 ТЕСТИРУЕМ: {nickname}")
        print("=" * 60)

        player = diagnoser.find_player_any_method(nickname)

        if player:
            print(f"✅ Игрок найден: {player['nickname']}")
        else:
            print(f"❌ Игрок не найден ни одним методом")

    diagnoser.check_api_limits()