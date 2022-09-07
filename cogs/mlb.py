import io
import discord
from discord.ext import commands
import aiohttp
from reportlab.graphics import renderPM
import datetime
from dateutil import parser, tz

from utils.mlb import convert_svg_to_png, get_player_stats, game_url, logo_url, player_stats_url, probables_url, score_url, standings_url
from utils.logger import log
from utils.date import get_datetime

from help.mlb import magic_long_help, probables_long_help, record_long_help, score_long_help

class MLB(commands.Cog, name='mlb', command_attrs=dict(hidden=False)):
  def __init__(self, bot):
    self.bot = bot
    self.from_utc_zone = tz.tzutc()
    self.to_zone = tz.tzlocal()

  @commands.command(name='logo', brief='Get a logo for an MLB team')
  async def get_logo(self, ctx, team: str):
    if team is None:
      msg = 'Team must be provided as the first argument'
      log(f'{msg} - CMD (logo)', False)
      await ctx.send(msg)
    team = team.lower()
    params = { 'abbreviation': team }
    async with aiohttp.ClientSession() as session:
      async with session.get(logo_url, params=params) as response:
        if response.content_type != 'application/json':
          embed = discord.Embed(title=f'{team.upper()} logo', description=f'{team.upper()} logo', url=f'{logo_url}?abbreviation={team}')
          png_image = io.BytesIO()
          try:
            renderPM.drawToFile(convert_svg_to_png(io.StringIO(await response.text())), png_image, fmt='PNG',  configPIL={'transparent': None})
          except:
            log('Logo SVG to PNG failed - CMD (logo)', False)
          embed.set_author(name='sportscord')
          embed.set_image(url=f'attachment://{team}.png')
          embed.set_footer(text='Courtesy of Sports Stats API and MLB.')
          png_image.seek(0)
          log(f'Got {team.upper()} logo. - CMD (logo)', True)
          await ctx.send(file=discord.File(png_image, f'{team}.png'), embed=embed)
        else:
          jdata = await response.json()
          log(f'{jdata["message"]} - CMD (logo)')
          await ctx.send(jdata['message'])

  @commands.command(name='score', brief='Gets the score for a given team', help=score_long_help)
  async def get_score(self, ctx, team: str, date: str = None):
    if team is None:
      msg = f'Team must be provided as the first argument'
      log(f'{msg} - CMD (score)', False)
      await ctx.send(msg)
    else:
      team = team.lower()
      params = {
        'abbreviation': team,
      }
      if date is not None:
        params['date'] = get_datetime(date, 'mm/dd/yyyy')
      else:
        params['date'] = get_datetime('today', 'mm/dd/yyyy')

      exit_loop = False

      async with aiohttp.ClientSession() as session:
        async with session.get(game_url, params=params) as game_response:
          game_jdata = await game_response.json()
          if game_jdata['totalGames'] != 0:
            for game in game_jdata['games']:
              if game['status']['detailedState'] == 'Postponed':
                exit_loop = True
                away_team = game['teams']['away']['team']
                home_team = game['teams']['home']['team']
                away_abbr = away_team['abbreviation']
                home_abbr = home_team['abbreviation']
                away_record = f'{game["teams"]["away"]["leagueRecord"]["wins"]}-{game["teams"]["away"]["leagueRecord"]["losses"]}'
                home_record = f'{game["teams"]["home"]["leagueRecord"]["wins"]}-{game["teams"]["home"]["leagueRecord"]["losses"]}'

                game_time_utc = parser.isoparse(game['rescheduleDate'])
                game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
                game_time_local_tz = game_time_utc.astimezone(self.to_zone)
                game_time_local_tz = datetime.datetime.strftime(game_time_local_tz, "%m/%d/%Y %#I:%M %p")
                await ctx.send(f'Postponed ({game["status"]["reason"]}) | {away_abbr} ({away_record}) vs. {home_abbr} ({home_record}) | Rescheduled time: {game_time_local_tz}')
            
            if exit_loop == True:
              return
            else:
              async with session.get(score_url, params=params) as response:
                jdata = await response.json()
                return_str: str
                for game in jdata:
                  game_status = game['status']
                  game_status_code = game_status['codedGameState']
                  game_status_detail = game_status['detailedState']

                  linescore = game['linescore']
                  away_team = game['away']
                  away_abbr = away_team['abbreviation']
                  away_record = f'{away_team["record"]["wins"]}-{away_team["record"]["losses"]}'
                  home_team = game['home']
                  home_abbr = home_team['abbreviation']
                  home_record = f'{home_team["record"]["wins"]}-{home_team["record"]["losses"]}'
                  if game_status_code != 'I' and game_status_code != 'F'and game_status_code != 'G' and game_status_code != 'O':
                    game_time_utc = parser.isoparse(game['datetime']['dateTime'])
                    game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
                    game_time_local_tz = game_time_utc.astimezone(self.to_zone)
                    game_time_local_tz = datetime.datetime.strftime(game_time_local_tz, "%#I:%M %p")
                    game_time = game_time_local_tz if game_status['startTimeTBD'] == False else 'TBD'
                    return_str = f'{game_status_detail} | {away_abbr} ({away_record}) vs. {home_abbr} ({home_record}) | {game_time}'
                  elif game_status_code == 'I':
                    inning_half = linescore['inningState']
                    inning = linescore['currentInningOrdinal']
                    away_score = linescore['teams']['away']['runs']
                    home_score = linescore['teams']['home']['runs']
                    return_str = f'{inning_half} {inning} | {away_abbr}: {away_score} vs. {home_abbr}: {home_score}'
                  else:
                    inning = linescore['currentInning']
                    away_score = linescore['teams']['away']['runs']
                    home_score = linescore['teams']['home']['runs']

                    if home_score > away_score:
                      home_result = f'**{home_abbr} ({home_record}): {home_score}**'
                      away_result = f'{away_abbr} ({away_record}): {away_score}'
                    else:
                      home_result = f'{home_abbr} ({home_record}): {home_score}'
                      away_result = f'**{away_abbr} ({away_record}): {away_score}**'

                    status_str = 'FINAL' if inning == 9 else f'FINAL/{inning}'
                    return_str = f'{status_str} | {away_result} vs. {home_result}'

                  await ctx.send(return_str)
            log(f'Got score for {team.upper()}. - CMD (score)', True)
          else:
            today = datetime.date.today()
            msg = f'No games found for {team.upper()} on {today.strftime("%m/%d/%y")}!'
            log(f'{msg} - CMD (score)', True)
            await ctx.send(msg)

  @commands.command(name='record', brief='Gets the record for a team', help=record_long_help)
  async def get_record(self, ctx, team: str, date: str = None):
    if team is None:
      msg = 'Team must be provided as the first argument'
      log(f'{msg} - CMD (record)')
      await ctx.send(msg)
    else:
      params = {
        'abbreviation': team,
      }

      today = datetime.date.today()
      if date is None:
        params['year'] = today.year
      
      if '/' in date:
        params['date'] = date
      else:
        params['date'] = get_datetime(date, 'mm/dd/yyyy')

      async with aiohttp.ClientSession() as session:
        async with session.get(standings_url, params=params) as response:
          jdata = await response.json()
          if 'message' in jdata is None:
            log(f'{jdata["message"]} - CMD (record)', False)
            await ctx.send(jdata['message'])
          else:
            league_record = jdata['leagueRecord']

            standings_str = f'{team.upper()}: {league_record["wins"]}-{league_record["losses"]}'
            await ctx.send(standings_str)
  
  @commands.command(name='magic', brief='Gets the magic number for a team', help=magic_long_help)
  async def get_magic_number(self, ctx, team: str, year: str = None):
    if team is None:
      msg = 'Team must be provided as the first argument'
      log(f'{msg} - CMD (magic)')
      await ctx.send(msg)
    else:
      params = {
        'abbreviation': team,
      }

      today = datetime.date.today()
      if year is None:
        params['year'] = today.year

      async with aiohttp.ClientSession() as session:
        async with session.get(standings_url, params=params) as response:
          jdata = await response.json()
          if 'message' in jdata is None:
            log(f'{jdata["message"]} - CMD (magic)', False)
            await ctx.send(jdata['message'])
          else:
            elimination_number = jdata['eliminationNumber']
            wc_elimination_number = jdata['wildCardEliminationNumber']

            magic_num_str: str

            if 'magicNumber' in jdata is not None:
              magic_num_str = f'{team.upper()}\n**MAGIC NUMBER**: {jdata["magicNumber"]}'
            else:
              magic_num_str = f'{team.upper()}\n**DIVISION ELIMINATION NUMBER**: {elimination_number}\n**WILD CARD ELIMINATION NUMBER**: {wc_elimination_number}'

            await ctx.send(magic_num_str)
  
  @commands.command(name='probables', brief='Gets the pitching probables for a game', help=probables_long_help)
  async def get_probables(self, ctx, team: str, date: str = None):
    if team is None:
      msg = f'Team must be provided as the first argument'
      log(f'{msg} - CMD (probables)', False)
      await ctx.send(msg)
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
        async with session.get(score_url, params=params) as games_response:
          game_jdata = await games_response.json()

      async with aiohttp.ClientSession() as session:
        async with session.get(probables_url, params=params) as response:
          jdata = await response.json()
          if len(jdata) != 0:
            return_str: str
            for i, game in enumerate(jdata):
              probables = game['probables']

              away_abbreviation = probables['awayAbbreviation']
              home_abbreviation = probables['homeAbbreviation']
              away_pitcher = probables['awayProbable']
              home_pitcher = probables['homeProbable']

              away_params = {
                'id': away_pitcher
              }

              home_params = {
                'id': home_pitcher
              }
              
              current_year = get_datetime(date, 'json')
              if away_pitcher is not None:
                async with session.get(player_stats_url, params=away_params) as away_response:
                  away_jdata = await away_response.json()
                  away_pitcher_stats = get_player_stats(away_jdata['people'][0]['stats'], 'yearByYear')
                  for j in away_pitcher_stats['splits']:
                    if j['season'] == current_year['year']: current_away_pitcher_data = j; break
                  if away_pitcher_stats == None:
                    msg = f'Could not pitcher stats for {team.upper()}'
                    log(f'{msg} - CMD (probables)', True)
                    await ctx.send(msg)
              
              if home_pitcher is not None:
                async with session.get(player_stats_url, params=home_params) as home_response:
                  home_jdata = await home_response.json()
                  home_pitcher_stats = get_player_stats(home_jdata['people'][0]['stats'], 'yearByYear')
                  for j in home_pitcher_stats['splits']:
                    if j['season'] == current_year['year']: current_home_pitcher_data = j; break
                  if home_pitcher_stats == None:
                    msg = f'Could not pitcher stats for {team.upper()}'
                    log(f'{msg} - CMD (probables)', True)
                    await ctx.send(msg)

              away_pitcher_str = 'TBD'
              home_pitcher_str = 'TBD'
              if away_pitcher is not None:
                away_pitcher_name = away_jdata['people'][0]['fullName'] if away_pitcher is not None else 'TBD'
                away_pitcher_era = current_away_pitcher_data['stat']['era']
                away_pitcher_str = f'{away_pitcher_name} ({away_pitcher_era} ERA)'
              if home_pitcher is not None:
                home_pitcher_name = home_jdata['people'][0]['fullName'] if home_pitcher is not None else 'TBD'
                home_pitcher_era = current_home_pitcher_data['stat']['era']
                home_pitcher_str = f'{home_pitcher_name} ({home_pitcher_era} ERA)'

              if len(game_jdata) != 0:
                game_time_utc = parser.isoparse(game_jdata[i]['datetime']['dateTime'])
                game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
                game_time_local_tz = game_time_utc.astimezone(self.to_zone)
                game_time_local_tz = datetime.datetime.strftime(game_time_local_tz, "%#I:%M %p")
              return_str = f'_{away_abbreviation} vs. {home_abbreviation}_ | {game_time_local_tz}\n{away_pitcher_str} vs. {home_pitcher_str}'

              await ctx.send(return_str)
            log(f'Got probables for {team.upper()}. - CMD (probables)', True)
          else:
            today = datetime.date.today()
            msg = f'No games found for {team.upper()} on {today.strftime("%m/%d/%y")}!'
            log(f'{msg} - CMD (probables)', True)
            await ctx.send(msg)

async def setup(bot):
  await bot.add_cog(MLB(bot))