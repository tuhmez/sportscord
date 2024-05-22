from array import array
from svglib.svglib import svg2rlg

def convert_svg_to_png(svg_code):
  return svg2rlg(path=svg_code)

def get_player_stats(player_stats, stat_type):
  if stat_type != 'yearByYear' and stat_type != 'yearByYearAdvanced' and stat_type != 'career' and stat_type != 'careerAdvanced' and type != 'firstYearStats' and stat_type != 'lastYearStats' and stat_type != 'gameTypeStats':
    return None
  
  if player_stats is None:
    return None

  stats = None
  for i in player_stats:
    if i['type']['displayName'] == stat_type:
      stats = i
      break

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

def get_ordinal(number: int):
  if number == 1:
    return '1st'
  elif number == 2:
    return '2nd'
  elif number == 3:
    return '3rd'
  elif number == 4:
    return '4th'
  else:
    return '5th'
  
def translate_specific_type_to_general_type_for_standings(specific_type: str):
  if specific_type.lower() == 'al' or specific_type.lower() == 'nl':
    return 'league'
  elif specific_type.lower().startswith('playoff') == True:
    return 'playoff'
  else:
    return 'division'

def translate_long_division_to_abbreviation(long_division: str):
  if long_division == 'American League Central':
    return 'ALC'
  elif long_division == 'American League East':
    return 'ALE'
  elif long_division == 'American League West':
    return 'ALW'
  elif long_division == 'National League Central':
    return 'NLC'
  elif long_division == 'National League East':
    return 'NLE'
  elif long_division == 'National League West':
    return 'NLW'
  else:
    return 'N/A'

division_leaders_separator = '===='
wild_card_separator = '----'

def get_playoff_standing_str(league: str, division_leaders: array, wild_card: array):
  record_strings = []

  record_strings.append(league)

  for record in division_leaders:
    division_abbreviation =  translate_long_division_to_abbreviation(record['team']['division']['name'])
    division_abbreviation = division_abbreviation.replace(league.upper(), '')
    record_strings.append(f'{division_abbreviation} - {record['abbreviation']} ({record['wins']}-{record['losses']})')

  record_strings.append(division_leaders_separator * 5)

  ready_to_insert_wild_card_separator = False

  for record in wild_card:
    record_strings.append(f'{record['abbreviation']} ({record['wildCardGamesBack']}GB)')

    if record['wildCardRank'] == 3:
      ready_to_insert_wild_card_separator = True

    if ready_to_insert_wild_card_separator == True:
      record_strings.append(wild_card_separator * 6)
      ready_to_insert_wild_card_separator = False


  return '\n'.join(record_strings)