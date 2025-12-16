import sqlite3
from contextlib import closing
from config import Config


def init_db():
    """Инициализация базы данных"""
    with closing(get_db()) as db:
        with open('schema.sql', 'r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Получение соединения с БД"""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Создание таблиц"""
    conn = get_db()
    cursor = conn.cursor()

    # Таблица игроков
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        nickname TEXT NOT NULL,
        country TEXT,
        avatar TEXT,
        skill_level INTEGER,
        faceit_elo INTEGER,
        game TEXT,
        created_at TIMESTAMP,
        last_updated TIMESTAMP
    )
    ''')

    # Таблица матчей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        match_id TEXT PRIMARY KEY,
        player_id TEXT,
        result TEXT,
        kills INTEGER,
        deaths INTEGER,
        kd_ratio REAL,
        hs_percent REAL,
        map_name TEXT,
        date TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    ''')

    # Таблица статистики
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_stats (
        player_id TEXT PRIMARY KEY,
        total_matches INTEGER,
        wins INTEGER,
        losses INTEGER,
        win_rate REAL,
        avg_kills REAL,
        avg_deaths REAL,
        avg_kd REAL,
        avg_hs REAL,
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    ''')

    conn.commit()
    conn.close()