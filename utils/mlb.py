from svglib.svglib import svg2rlg

def convert_svg_to_png(svg_code):
  return svg2rlg(path=svg_code)

def get_player_stats(player_stats, stat_type):
  if stat_type != 'yearByYear' and stat_type != 'yearByYearAdvanced' and stat_type != 'career' and stat_type != 'careerAdvanced' and type != 'firstYearStats' and stat_type != 'lastYearStats' and stat_type != 'gameTypeStats':
    return None

  for i in player_stats:
    if i['type']['displayName'] == stat_type: stats = i; break

  return stats
