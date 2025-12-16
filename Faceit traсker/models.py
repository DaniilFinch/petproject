from datetime import datetime

class Player:
    def __init__(self, player_id, nickname, country, avatar, skill_level, faceit_elo, game):
        self.player_id = player_id
        self.nickname = nickname
        self.country = country
        self.avatar = avatar
        self.skill_level = skill_level
        self.faceit_elo = faceit_elo
        self.game = game
        self.created_at = datetime.now()

class Match:
    def __init__(self, match_id, player_id, result, kills, deaths, kd_ratio, hs_percent, map_name, date):
        self.match_id = match_id
        self.player_id = player_id
        self.result = result  # 'win' или 'loss'
        self.kills = kills
        self.deaths = deaths
        self.kd_ratio = kd_ratio
        self.hs_percent = hs_percent
        self.map_name = map_name
        self.date = date

class PlayerStats:
    def __init__(self, player_id, total_matches, wins, losses, win_rate, avg_kills, avg_deaths, avg_kd, avg_hs):
        self.player_id = player_id
        self.total_matches = total_matches
        self.wins = wins
        self.losses = losses
        self.win_rate = win_rate
        self.avg_kills = avg_kills
        self.avg_deaths = avg_deaths
        self.avg_kd = avg_kd
        self.avg_hs = avg_hs