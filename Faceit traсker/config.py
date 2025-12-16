# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'test')

    # База данных
    DATABASE = 'faceit_data.db'

    # ★★★ ВАЖНО: FACEIT API КЛЮЧ ★★★
    # Получите на https://developers.faceit.com/apps
    # Создайте приложение и скопируйте API Key
    FACEIT_API_KEY = os.environ.get('FACEIT_API_KEY', 'c60fb845-a4a7-4bda-beb6-1030a921424d')

    # URL API
    FACEIT_API_URL = 'https://open.faceit.com/data/v4'

    # Игра (можно менять)
    # 'cs2' - Counter-Strike 2
    # 'csgo' - Counter-Strike: Global Offensive
    # 'valorant' - Valorant
    FACEIT_GAME = 'cs2'

    @classmethod
    def print_info(cls):
        print("\n" + "=" * 60)
        print("FACEIT ANALYSER CONFIGURATION")
        print("=" * 60)
        print(f"🔑 API Key: {'✅ SET' if cls.FACEIT_API_KEY else '❌ NOT SET'}")
        if cls.FACEIT_API_KEY:
            print(f"   Key: {cls.FACEIT_API_KEY[:15]}...")
        print(f"🌐 API URL: {cls.FACEIT_API_URL}")
        print(f"🎮 Game: {cls.FACEIT_GAME}")
        print("=" * 60)

        if not cls.FACEIT_API_KEY:
            print("\n⚠️  WARNING: No API key configured!")
            print("\nTo get API key:")
            print("1. Go to https://developers.faceit.com")
            print("2. Sign in with your FACEIT account")
            print("3. Click 'App Studio' → 'Create New App'")
            print("4. Copy 'API Key'")
            print("5. Create .env file and add:")
            print("   FACEIT_API_KEY=your_key_here")
            print("\nRunning in LIMITED mode without API key.")