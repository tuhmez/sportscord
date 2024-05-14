from svglib.svglib import svg2rlg

def convert_svg_to_png(svg_code):
  return svg2rlg(path=svg_code)

def get_player_stats(player_stats, stat_type):
  if stat_type != 'yearByYear' and stat_type != 'yearByYearAdvanced' and stat_type != 'career' and stat_type != 'careerAdvanced' and type != 'firstYearStats' and stat_type != 'lastYearStats' and stat_type != 'gameTypeStats':
    return None

  for i in player_stats:
    if i['type']['displayName'] == stat_type: stats = i; break

  return stats

def get_probable_statline(home_pitcher, away_pitcher, home_jdata, away_jdata, current_home_pitcher_data, current_away_pitcher_data):
  away_pitcher_str = 'TBD'
  home_pitcher_str = 'TBD'
  if away_pitcher is not None and away_jdata is not None and current_away_pitcher_data is not None:
    away_pitcher_name = away_jdata['people'][0]['fullName'] if away_pitcher is not None else 'TBD'
    away_pitcher_era = current_away_pitcher_data['stat']['era']
    away_pitcher_wins = current_away_pitcher_data['stat']['wins']
    away_pitcher_losses = current_away_pitcher_data['stat']['losses']
    away_pitcher_str = f'{away_pitcher_name} ({away_pitcher_wins}-{away_pitcher_losses} {away_pitcher_era} ERA)'
  if home_pitcher is not None and home_jdata is not None and current_home_pitcher_data is not None:
    home_pitcher_name = home_jdata['people'][0]['fullName'] if home_pitcher is not None else 'TBD'
    home_pitcher_era = current_home_pitcher_data['stat']['era']
    home_pitcher_wins = current_home_pitcher_data['stat']['wins']
    home_pitcher_losses = current_home_pitcher_data['stat']['losses']
    home_pitcher_str = f'{home_pitcher_name} ({home_pitcher_wins}-{home_pitcher_losses} {home_pitcher_era} ERA)'

  return { 'home_pitcher_str': home_pitcher_str, 'away_pitcher_str': away_pitcher_str }
