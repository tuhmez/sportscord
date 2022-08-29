from typing import Any
from svglib.svglib import svg2rlg

logo_url = 'https://sports-stats-api.herokuapp.com/mlb/team/logo'
boxscore_url = 'https://sports-stats-api.herokuapp.com/mlb/game/boxscore'
feed_url = 'https://sports-stats-api.herokuapp.com/mlb/game/feed'
score_url = 'https://sports-stats-api.herokuapp.com/mlb/game/score'
standings_url = 'https://sports-stats-api.herokuapp.com/mlb/standings'
probables_url = 'https://sports-stats-api.herokuapp.com/mlb/game/probables'
player_stats_url = 'https://sports-stats-api.herokuapp.com/mlb/player/stats'

def convert_svg_to_png(svg_code):
  return svg2rlg(path=svg_code)

def get_player_stats(player_stats, stat_type):
  if stat_type != 'yearByYear' and stat_type != 'yearByYearAdvanced' and stat_type != 'career' and stat_type != 'careerAdvanced' and type != 'firstYearStats' and stat_type != 'lastYearStats' and stat_type != 'gameTypeStats':
    return None

  for i in player_stats:
    if i['type']['displayName'] == stat_type: stats = i; break

  return stats
