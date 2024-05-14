import io
import aiohttp
import datetime
from reportlab.graphics import renderPM

from urls.mlb import game_url, games_url, logo_url, matchup_graphic_url, player_stats_url, probables_url, score_url, standings_url, team_url
from utils.mlb import convert_svg_to_png
from utils.date import get_datetime

async def get_logo_request(team: str, format: str):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = 'Team must be provided as the first argument'
    result['isOK'] = False
    return result
  else:
    params = { 'abbreviation': team.lower(), 'format': format.lower() }
    async with aiohttp.ClientSession() as session:
      async with session.get(logo_url, params=params) as response:
        if response.content_type != 'application/json':
          if format == 'png':
            result['data'] = io.BytesIO(await response.read())
            return result
          else:
            try:
              png_image = io.BytesIO()
              renderPM.drawToFile(convert_svg_to_png(io.StringIO(await response.text())), png_image, fmt='PNG', configPIL={'transparent': None })
              result['data'] = png_image
              return result
            except:
              result['msg'] = 'Logo SVG to PNG failed - CMD (logo)'
              result['isOK']  = False
              return result
        else:
          result['msg'] = f'{await response.json()} - CMD (logo)'
          result['isOK'] = False
          return result

async def get_game_request(team: str, date: str = None):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = f'Team must be provided as the first argument'
    result['isOK'] = False
    return result
  else:
    team = team.lower()
    params = {
      'abbreviation': team,
    }
    if date is not None:
      params['date'] = get_datetime(date, 'mm/dd/yyyy')
    else:
      params['date'] = get_datetime('today', 'mm/dd/yyyy')

    async with aiohttp.ClientSession() as session:
      async with session.get(game_url, params=params) as game_response:
        result['data'] = await game_response.json()
        return result

async def get_score_request(team: str, date: str = None):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = f'Team must be provided as the first argument'
    result['isOK'] = False
    return result
  else:
    team = team.lower()
    params = {
      'abbreviation': team,
    }
    if date is not None:
      params['date'] = get_datetime(date, 'mm/dd/yyyy')
    else:
      params['date'] = get_datetime('today', 'mm/dd/yyyy')
    async with aiohttp.ClientSession() as session:
      async with session.get(score_url, params=params) as game_response:
        result['data'] = await game_response.json()
        return result

async def get_record_request(team: str, date: str = None):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = 'Team must be provided as the first argument'
    result['isOK'] = False
    return result
  else:
    params = {
      'abbreviation': team.lower(),
    }

    today = datetime.date.today()
    if date is None:
      params['year'] = today.year
    else:
      if date is not None:
        params['date'] = get_datetime(date, 'mm/dd/yyyy')
      else:
        params['date'] = get_datetime('today', 'mm/dd/yyyy')

    async with aiohttp.ClientSession() as session:
      async with session.get(standings_url, params=params) as standings_response:
        result['data'] = await standings_response.json()
        return result
      
async def get_magic_number_request(team: str, year: str = None):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = 'Team must be provided as the first argument'
    result['isOK'] = False
    return result
  else:
    params = {
      'abbreviation': team,
    }

    today = datetime.date.today()
    if year is None:
      params['year'] = today.year

    async with aiohttp.ClientSession() as session:
      async with session.get(standings_url, params=params) as standings_response:
        jdata = await standings_response.json()
        if 'message' in jdata is None:
          result['msg'] = jdata['message']
          result['isOK'] = False
          return result
        else:
          result['data'] = jdata
          return result

async def get_probables_request(team: str, date: str):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = f'Team must be provided as the first argument'
    result['isOK'] = False
    await result
  else:
    team = team.lower()
    params = {
      'abbreviation': team,
    }
    if date is not None:
      date = get_datetime(date, 'mm/dd/yyyy')
      params['date'] = date
    else:
      date = get_datetime('today', 'mm/dd/yyyy')
      params['date'] = date

    async with aiohttp.ClientSession() as session:
      async with session.get(probables_url, params=params) as probables_response:
        result['data'] = await probables_response.json()
        return result

async def get_player_stats_request(id: str):
  result = { 'msg': '', 'isOK': True }

  if id is '':
    result['msg'] = 'Player ID invalid'
    result['isOK'] = False
    return result
  else:
    params = { 'id': id }
    async with aiohttp.ClientSession() as session:
      async with session.get(player_stats_url, params=params) as player_response:
        result['data'] = await player_response.json()
        return result

async def get_games_request(date: str = None):
  result = { 'msg': '', 'isOK': True }
  params = {
    'date': get_datetime(date if date is not None else 'today', 'mm/dd/yyyy')
  }
  
  async with aiohttp.ClientSession() as session:
    async with session.get(games_url, params=params) as game_response:
      result['data'] = await game_response.json()
      return result

async def get_team_request(team: str):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = 'Team must be provided as the first argument'
    result['isOK'] = False
    return result
  else:
    params = {
      'abbreviation': team.lower(),
    }

    async with aiohttp.ClientSession() as session:
      async with session.get(team_url, params=params) as team_response:
        result['data'] = await team_response.json()
        return result

async def get_matchup_graphic_request(team: str, date: str = None):
  result = { 'msg': '', 'isOK': True }

  if team is None:
    result['msg'] = 'Team must be provided as the first argument'
    result['isOK'] = False
    return result
  team = team.lower()
  params = {
    'date': get_datetime(date if date is not None else 'today', 'mm/dd/yyyy'),
    'abbreviation': team
  }

  async with aiohttp.ClientSession() as session:
    async with session.get(matchup_graphic_url, params=params) as matchup_graphic_response:
      result['data'] = io.BytesIO(await matchup_graphic_response.read())
      return result