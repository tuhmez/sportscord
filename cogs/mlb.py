import discord
from discord.ext import commands, tasks
import datetime
from dateutil import parser, tz

from urls.mlb import boxscore_url, logo_url, ext_gameday_url
from utils.mlb import get_ordinal, get_player_stats, get_probable_statline, translate_specific_type_to_general_type_for_standings, translate_long_division_to_abbreviation, get_playoff_standing_str
from utils.logger import log
from utils.date import get_datetime

from help.mlb import games_long_help, magic_long_help, matchup_long_help, probables_long_help, record_long_help, score_long_help, standings_long_help

from workers.mlb import get_feed_request, get_game_request, get_games_request, get_logo_request, get_magic_number_request, get_matchup_graphic_request, get_player_stats_request, get_probables_request, get_record_request, get_score_request, get_standings_request, get_team_request

class MLB(commands.Cog, name='mlb', command_attrs=dict(hidden=False)):
  def __init__(self, bot):
    self.bot: commands.Bot = bot
    self.from_utc_zone = tz.tzutc()
    self.to_zone = tz.tzlocal()
    self.current_play_id = None
    self.running_tasks = {}

  @commands.command(name='logo', brief='Get a logo for an MLB team')
  async def get_logo(self, ctx: commands.Context, team: str):
    logo_result = await get_logo_request(team, 'png')
    team_result = await get_team_request(team)
    if logo_result['isOK'] == False:
      log(logo_result['msg'], False)
      await ctx.send(logo_result['msg'])
    else:
      png_image = logo_result['data']
      title = team.upper()

      if team_result['isOK'] == True:
        team_jdata = team_result['data']
        title = f'{team_jdata['teams'][0]['franchiseName']} {team_jdata['teams'][0]['clubName']}'
      embed = discord.Embed(title=f'{title} logo', description=f'{title} logo', url=f'{logo_url}?abbreviation={team.lower()}')
      embed.set_author(name='sportscord')
      embed.set_image(url=f'attachment://{team}.png')
      embed.set_footer(text='Courtesy of Sports Stats API and MLB.')
      png_image.seek(0)
      log(f'Got {team.upper()} logo. - CMD (logo)', True)
      await ctx.send(file=discord.File(png_image, f'{team}.png'), embed=embed)

  @commands.command(name='score', brief='Gets the score for a given team', help=score_long_help)
  async def get_score(self, ctx: commands.Context, team: str, date: str = None):
      game_response = await get_game_request(team, date)
      exit_loop = False
      if game_response['isOK'] == False:
        log(game_response['msg'], False)
        await ctx.send(game_response['msg'])
      else:
        game_jdata = game_response['data']
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
            score_response = await get_score_request(team, date)
            if score_response['isOK'] == False:
              log(score_response['msg'], False)
              await ctx.send(score_response['msg'])
            else:
              jdata = score_response['data']
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
          if date is None:
            date = get_datetime('today', 'mm/dd/yyyy')
          else:
            date = get_datetime(date, 'mm/dd/yyyy')
          msg = f'No games found for {team.upper()} on {date}!'
          log(f'{msg} - CMD (score)', True)
          await ctx.send(msg)

  @commands.command(name='record', brief='Gets the record for a team', help=record_long_help)
  async def get_record(self, ctx: commands.Context, team: str, date: str = None):
    record_response = await get_record_request(team, date)

    if record_response['isOK'] == False:
      log(record_response['msg'], False)
      await ctx.send(record_response['msg'])
    else:
      jdata = record_response['data']
      if 'message' in jdata is None:
        log(f'{jdata["message"]} - CMD (record)', False)
        await ctx.send(jdata['message'])
      else:
        division = jdata['team']['division']['name']
        divisionGamesBack = jdata['divisionGamesBack']

        ordinal = get_ordinal(jdata['divisionRank'])
        if jdata['divisionRank'] == '1':
          div_place = f'{ordinal} in {division}'
        elif jdata['divisionRank'] == '2':
          div_place = f'{ordinal} in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'
        elif jdata['divisionRank'] == '3':
          div_place = f'{ordinal} in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'
        elif jdata['divisionRank'] == '4':
          div_place = f'{ordinal} in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'
        else:
          div_place = f'{ordinal} in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'

        standings_str = f'{team.upper()}: {jdata["wins"]}-{jdata["losses"]}, {div_place}'
        await ctx.send(standings_str)
  
  @commands.command(name='magic', brief='Gets the magic number for a team', help=magic_long_help)
  async def get_magic_number(self, ctx: commands.Context, team: str, year: str = None):
    magic_number_response = await get_magic_number_request(team, year)
    if magic_number_response['isOK'] == False:
      log(magic_number_response['msg'], False)
      await ctx.send(magic_number_response['msg'])
    else:
      magic_number_jdata = magic_number_response['data']
      elimination_number = magic_number_jdata['eliminationNumber']
      wc_elimination_number = magic_number_jdata['wildCardEliminationNumber']

      magic_num_str: str

      if 'magicNumber' in magic_number_jdata is not None:
        magic_num_str = f'{team.upper()}\n**MAGIC NUMBER**: {magic_number_jdata["magicNumber"]}'
      else:
        magic_num_str = f'{team.upper()}\n**DIVISION ELIMINATION NUMBER**: {elimination_number}\n**WILD CARD ELIMINATION NUMBER**: {wc_elimination_number}'

      await ctx.send(magic_num_str)
  
  @commands.command(name='probables', brief='Gets the pitching probables for a game', help=probables_long_help)
  async def get_probables(self, ctx: commands.Context, team: str, date: str = None):
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

      game_response = await get_score_request(team, date)
      if game_response['isOK'] == False:
        log(game_response['msg'], False)
        await ctx.send(game_response['msg'])

      probables_response = await get_probables_request(team, date)
      if probables_response['isOK'] == False:
        log(probables_response['msg'], False)
        await ctx.send(probables_response['msg'])

      game_jdata = game_response['data']
      probables_jdata = probables_response['data']

      if len(probables_jdata) != 0:
        return_str: str
        for i, game in enumerate(probables_jdata):
          probables = game['probables']

          away_abbreviation = probables['awayAbbreviation']
          home_abbreviation = probables['homeAbbreviation']
          away_pitcher = probables['awayProbable']
          home_pitcher = probables['homeProbable']
          
          current_year = get_datetime(date, 'json')

          current_away_pitcher_data = None
          away_jdata = None
          away_pitcher_stats = None

          if away_pitcher is not None:
            away_response = await get_player_stats_request(away_pitcher)

            if away_response['isOK'] == False:
              log(away_response['msg'], False)
              await ctx.send(away_response['msg'])
            else:
              away_jdata = away_response['data']
              if away_jdata['people'][0]['stats'] is not None:
                away_pitcher_stats = get_player_stats(away_jdata['people'][0]['stats'], 'yearByYear')

              if away_pitcher_stats is not None:
                for j in away_pitcher_stats['splits']:
                  if j['season'] == current_year['year']:
                    current_away_pitcher_data = j
                    break
                if away_pitcher_stats == None:
                  msg = f'Could not find pitcher stats for {team.upper()}'
                  log(f'{msg} - CMD (probables)', True)
                  await ctx.send(msg)
          
          current_home_pitcher_data = None
          home_jdata = None
          home_pitcher_stats = None

          if home_pitcher is not None:
            home_response = await get_player_stats_request(home_pitcher)
            if home_response['isOK'] == False:
              log(home_response['msg'], False)
              await ctx.send(home_response['msg'])
            else:
              home_jdata = home_response['data']
              print(home_jdata['people'][0])
              if home_jdata['people'][0]['stats'] is not None:
                home_pitcher_stats = get_player_stats(home_jdata['people'][0]['stats'], 'yearByYear')
              
              if home_pitcher_stats is not None:
                for j in home_pitcher_stats['splits']:
                  if j['season'] == current_year['year']:
                    current_home_pitcher_data = j
                    break
                if home_pitcher_stats == None:
                  msg = f'Could not find pitcher stats for {team.upper()}'
                  log(f'{msg} - CMD (probables)', True)
                  await ctx.send(msg)

          pitcher_statlines = get_probable_statline(home_pitcher=home_pitcher, away_pitcher=away_pitcher, home_jdata=home_jdata, away_jdata=away_jdata, current_home_pitcher_data=current_home_pitcher_data, current_away_pitcher_data=current_away_pitcher_data)
          if len(game_jdata) != 0:
            game_time_utc = parser.isoparse(game_jdata[i]['datetime']['dateTime'])
            game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
            game_time_local_tz = game_time_utc.astimezone(self.to_zone)
            game_time_local_tz = datetime.datetime.strftime(game_time_local_tz, "%#I:%M %p")
          return_str = f'_{away_abbreviation} vs. {home_abbreviation}_ | {game_time_local_tz}\n{pitcher_statlines['away_pitcher_str']} vs. {pitcher_statlines['home_pitcher_str']}'

          await ctx.send(return_str)
        log(f'Got probables for {team.upper()}. - CMD (probables)', True)
      else:
        date = datetime.datetime.strptime(params['date'], 'mm/dd/yyyy')
        msg = f'No games found for {team.upper()} on {date.strftime("%m/%d/%y")}!'
        log(f'{msg} - CMD (probables)', True)
        await ctx.send(msg)

  @commands.command(name='games', brief='Get all games for a day', help=games_long_help)
  async def get_games(self, ctx: commands.Context, date: str = None):
    params = {
      'date': get_datetime(date if date is not None else 'today', 'mm/dd/yyyy')
    }

    game_response = await get_games_request(date)

    if game_response['isOK'] == False:
      log(game_response['msg'], False)
      await ctx.send(game_response['msg'])
    else:
      game_jdata = game_response['data']
      if game_jdata['totalGames'] != 0:
        game_strings = []
        for game in game_jdata['dates'][0]['games']:
          return_str: str
          away_team = game['teams']['away']['team']
          home_team = game['teams']['home']['team']

          if away_team['sport']['id'] != 1 or home_team['sport']['id'] != 1:
            continue

          away_abbr = away_team['abbreviation']
          home_abbr = home_team['abbreviation']
          away_record = f'{game["teams"]["away"]["leagueRecord"]["wins"]}-{game["teams"]["away"]["leagueRecord"]["losses"]}'
          home_record = f'{game["teams"]["home"]["leagueRecord"]["wins"]}-{game["teams"]["home"]["leagueRecord"]["losses"]}'

          game_status = game['status']
          game_status_code = game_status['codedGameState']
          game_status_detail = game_status['detailedState']

          if game_status_code != 'I' and game_status_code != 'F'and game_status_code != 'G' and game_status_code != 'O':
            game_time_utc = parser.isoparse(game['gameDate'])
            game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
            game_time_local_tz = game_time_utc.astimezone(self.to_zone)
            game_time_local_tz = datetime.datetime.strftime(game_time_local_tz, "%#I:%M %p")
            game_time = game_time_local_tz if game_status['startTimeTBD'] == False else 'TBD'
            return_str = f'{game_status_detail} | {away_abbr} ({away_record}) vs. {home_abbr} ({home_record}) | {game_time}'
          elif game_status_code == 'I':
            linescore = game['linescore']
            inning_half = linescore['inningState']
            inning = linescore['currentInningOrdinal']
            away_score = linescore['teams']['away']['runs']
            home_score = linescore['teams']['home']['runs']
            return_str = f'{inning_half} {inning} | {away_abbr}: {away_score} vs. {home_abbr}: {home_score}'
          elif game_status_detail == 'Postponed':
            game_time_utc = parser.isoparse(game['rescheduleDate'])
            game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
            game_time_local_tz = game_time_utc.astimezone(self.to_zone)
            game_time_local_tz = datetime.datetime.strftime(game_time_local_tz, "%m/%d/%Y %#I:%M %p")
            return_str = f'Postponed ({game["status"]["reason"]}) | {away_abbr} ({away_record}) vs. {home_abbr} ({home_record}) | Rescheduled time: {game_time_local_tz}'
          else:
            linescore = game['linescore']
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
          game_strings.append(return_str)
        await ctx.send('\n'.join(game_strings))
        log(f'Got games. - CMD (score)', True)
      else:
        date = datetime.datetime.strptime(params['date'], 'mm/dd/yyyy')
        msg = f'No games found for {date.strftime("%m/%d/%y")}!'
        log(f'{msg} - CMD (score)', True)
        await ctx.send(msg)

  @commands.command(name='matchup', brief='Gets the game matchup by date', help=matchup_long_help)
  async def get_matchup(self, ctx: commands.Context, team: str, date: str = None):
    matchup_graphic_response = await get_matchup_graphic_request(team, date)
    score_response = await get_score_request(team, date)
    probables_response = await get_probables_request(team, date)

    if matchup_graphic_response['isOK'] == False:
      log(matchup_graphic_response['msg'], False)
      await ctx.send(matchup_graphic_response['msg'])
    else:
      matchup_graphic = matchup_graphic_response['data']

      title = f'{team.upper()} Matchup'
      description = title
      url = f'{boxscore_url}?abbreviation={team.lower()}'

      if date is not None:
        jdate = get_datetime(date, 'json')
        jdate['month'] = str(jdate['month']).rjust(2, '0')
        jdate['day'] = str(jdate['day']).rjust(2, '0')
      else:
        today = datetime.date.today()
        jdate = { 'month': str(today.month).rjust(2, '0'), 'day': str(today.day).rjust(2, '0'), 'year': today.year }

      if score_response['isOK'] == True:
        if len(score_response['data']) == 0:
          date = f'{jdate['month']}/{jdate['day']}/{jdate['year']}'
          msg = f'No games found for {team.upper()} on {date}!'
          await ctx.send(msg)
        else:
          game = score_response['data'][0]
          game_status = game['status']
          game_status_code = game_status['codedGameState']
          game_status_detail = game_status['detailedState']

          game_id = game['game']['pk']

          home_team = game['home']
          away_team = game['away']

          home_abbr = home_team['abbreviation'].upper()
          away_abbr = away_team['abbreviation'].upper()

          home_record = f'{home_team['record']['leagueRecord']['wins']}-{home_team['record']['leagueRecord']['losses']}'
          away_record = f'{away_team['record']['leagueRecord']['wins']}-{away_team['record']['leagueRecord']['losses']}'

          home_club_name = home_team['teamName'].lower().replace(' ', '-')
          away_club_name = away_team['teamName'].lower().replace(' ', '-')
          title = f'{away_team['name']} at {home_team['name']}'

          url = f'{ext_gameday_url}/{away_club_name}-vs-{home_club_name}/{jdate['year']}/{jdate['month']}/{jdate['day']}/{game_id}'

          linescore = game['linescore']

          if game_status_code != 'I' and game_status_code != 'F'and game_status_code != 'G' and game_status_code != 'O':
            url = f'{url}/preview'
            game_time_utc = parser.isoparse(game['datetime']['dateTime'])
            game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
            game_time_local_tz = game_time_utc.astimezone(self.to_zone)
            game_time_local_tz = datetime.datetime.strftime(game_time_local_tz, "%#I:%M %p")
            game_time = game_time_local_tz if game_status['startTimeTBD'] == False else 'TBD'

            probables_jdata = probables_response['data']

            if len(probables_jdata) != 0:
              for i, game in enumerate(probables_jdata):
                probables = game['probables']

                away_pitcher = probables['awayProbable']
                home_pitcher = probables['homeProbable']
                
                current_away_pitcher_data = None
                away_probables_jdata = None
                if away_pitcher is not None:
                  away_probable_stats_response = await get_player_stats_request(away_pitcher)

                  if away_probable_stats_response['isOK'] == True:
                    away_probables_jdata = away_probable_stats_response['data']
                    away_pitcher_stats = get_player_stats(away_probables_jdata['people'][0]['stats'], 'yearByYear')

                    if away_pitcher_stats is not None:
                      for j in away_pitcher_stats['splits']:
                        if f'{j['season']}' == f'{jdate['year']}': current_away_pitcher_data = j; break

                current_home_pitcher_data = None
                home_probables_jdata = None
                if home_pitcher is not None:
                  home_probable_stats_response = await get_player_stats_request(home_pitcher)
                  if home_probable_stats_response['isOK'] == True:
                    home_probables_jdata = home_probable_stats_response['data']
                    home_pitcher_stats = get_player_stats(home_probables_jdata['people'][0]['stats'], 'yearByYear')

                    if home_pitcher_stats is not None:
                      for j in home_pitcher_stats['splits']:
                        if f'{j['season']}' == f'{jdate['year']}': current_home_pitcher_data = j; break

            pitcher_statlines = get_probable_statline(home_pitcher=home_pitcher, away_pitcher=away_pitcher, home_jdata=home_probables_jdata, away_jdata=away_probables_jdata, current_home_pitcher_data=current_home_pitcher_data, current_away_pitcher_data=current_away_pitcher_data)

            description = f'{game_status_detail} | {away_abbr} ({away_record}) vs. {home_abbr} ({home_record}) | {game_time}\n\n{pitcher_statlines['away_pitcher_str']} vs. {pitcher_statlines['home_pitcher_str']}'
          elif game_status_code == 'I':
            inning = linescore['currentInning']
            inning_half = linescore['inningState']
            inning = linescore['currentInningOrdinal']
            away_score = linescore['teams']['away']['runs']
            home_score = linescore['teams']['home']['runs']
            description = f'{inning_half} {inning} | {away_abbr}: {away_score} vs. {home_abbr}: {home_score}'
          else:
            url = f'{url}/final/wrap'
            inning = linescore['currentInning']
            home_score = linescore['teams']['home']['runs']
            away_score = linescore['teams']['away']['runs']
            if home_score > away_score:
              home_result = f'**{home_abbr} ({home_record}): {home_score}**'
              away_result = f'{away_abbr} ({away_record}): {away_score}'
            else:
              home_result = f'{home_abbr} ({home_record}): {home_score}'
              away_result = f'**{away_abbr} ({away_record}): {away_score}**'

            status_str = 'FINAL' if inning == 9 else f'FINAL/{inning}'
            description = f'{status_str} | {away_result} vs. {home_result}'

          embed = discord.Embed(title=title, description=description, url=url)
          embed.set_author(name='sportscord')
          embed.set_image(url=f'attachment://{away_abbr.lower()}-vs-{home_abbr.lower()}.png')
          embed.set_footer(text='Courtesy of Sports Stats API and MLB.')
          matchup_graphic.seek(0)
          log(f'Got matchup for {team.upper()}', True)
          await ctx.send(file=discord.File(matchup_graphic, f'{away_abbr.lower()}-vs-{home_abbr.lower()}.png'), embed=embed)

  @commands.command(name='standings', brief='Gets the standings for a division, conference, league, or wild card', help=standings_long_help)
  async def get_standings(self, ctx: commands.Context, specific_type: str, conf_div_or_date: str = None, date: str = None):
    if specific_type is None:
      msg = 'A type must be provided! Valid types are division or league abbreviations or the keyword \'playoff\''
      log(msg, False)
      await ctx.send(msg)
    else:
      standings_type = translate_specific_type_to_general_type_for_standings(specific_type)

      if specific_type.lower().startswith('playoff') == True:
        if conf_div_or_date is not None and conf_div_or_date.find('/') != -1:
          date = conf_div_or_date
      else:
        if conf_div_or_date is not None:
          date = conf_div_or_date

      standings_response = await get_standings_request(standings_type=standings_type, specific_type=specific_type if standings_type == 'division' or standings_type == 'league' else conf_div_or_date, date=date)

      if standings_response['isOK'] == False:
        log(standings_response['msg'], False)
        await ctx.send(standings_response['msg'])
      else:
        jdata = standings_response['data']
        if 'message' in jdata is None:
          log(f'{jdata["message"]} - CMD (standings)', False)
          await ctx.send(jdata['message'])
        else:
          record_strings = []

          print(standings_type)
          if standings_type.lower().startswith('playoff') == True:
            records = jdata['records']
            pref_conf = conf_div_or_date
            if pref_conf is None:
              al_division_leader_records = records[2]['teamRecords']
              al_wild_card_records = records[0]['teamRecords']
              nl_division_leader_records = records[3]['teamRecords']
              nl_wild_card_records = records[1]['teamRecords']

              al_playoff_str = get_playoff_standing_str('AL', al_division_leader_records, al_wild_card_records)
              nl_playoff_str = get_playoff_standing_str('NL', nl_division_leader_records, nl_wild_card_records)

              record_strings.append(al_playoff_str)
              record_strings.append('\n')
              record_strings.append(nl_playoff_str)
            else:
              if pref_conf.lower().startswith('al') == True:
                al_division_leader_records = records[1]['teamRecords']
                al_wild_card_records = records[0]['teamRecords']

                record_strings.append(get_playoff_standing_str('AL', al_division_leader_records, al_wild_card_records))
              elif pref_conf.lower().startswith('nl') == True:
                nl_division_leader_records = records[1]['teamRecords']
                nl_wild_card_records = records[0]['teamRecords']

                record_strings.append(get_playoff_standing_str('NL', nl_division_leader_records, nl_wild_card_records))
              else:
                msg = 'Specific type not recognized; for playoff standings, be sure to use either \'AL\' or \'NL\''
                log(msg, False)
                await ctx.send(msg)
          else:
            records = jdata['records'][0]['teamRecords']
            for record in records:
              record_str = f'{record['abbreviation']} ({record['wins']}-{record['losses']})'

              if standings_type is None or standings_type == 'division':
                if record['divisionLeader'] == False:
                  record_str = f'{record_str} ({record['divisionGamesBack']}GB)'
              else:
                record_str = f'{record_str} ({record['leagueGamesBack']}GB) ({record['wildCardGamesBack']}WCGB)'


              if record['clinched'] == True:
                record_str = f'{record['clinchIndicator']} - {record_str}'
              record_strings.append(record_str)
          
          await ctx.send('\n'.join(record_strings))
          log(f'Got standings for - type: {specific_type}, specific_type: {specific_type}, date: {date}', True)

  async def get_current_play(self, ctx: commands.Context, channel_id: int, team: str, game_index: int = 0):
    game_channel = ctx.guild.get_channel(channel_id)
    game_feed_response = await get_feed_request(team)

    if game_feed_response['isOK'] == True:
      games = game_feed_response['data']

      subscribed_game = games[game_index]

      game_data = subscribed_game['gameData']
      live_data = subscribed_game['liveData']
      linescore = live_data['linescore']

      away_team_game_data = game_data['teams']['away']
      home_team_game_data = game_data['teams']['home']

      away_team_abbr = away_team_game_data['abbreviation']
      away_team_record = f'{away_team_game_data['record']['wins']}-{away_team_game_data['record']['losses']}'

      home_team_abbr = home_team_game_data['abbreviation']
      home_team_record = f'{home_team_game_data['record']['wins']}-{home_team_game_data['record']['losses']}'

      away_linescore = linescore['teams']['away']
      home_linescore = linescore['teams']['home']

      game_status = game_data['status']

      if game_status['statusCode'] == 'F':
        inning = linescore['currentInning']
        status_str = 'FINAL' if inning == 9 else f'FINAL/{inning}'
        if home_linescore['runs'] > away_linescore['runs']:
          home_result = f'**{home_team_abbr} ({home_team_record}): {home_linescore['runs']}**'
          away_result = f'{away_team_abbr} ({away_team_record}): {away_linescore['runs']}'
        else:
          home_result = f'{home_team_abbr} ({home_team_record}): {home_linescore['runs']}'
          away_result = f'**{away_team_abbr} ({away_team_record}): {away_linescore['runs']}**'

        status_str = 'FINAL' if inning == 9 else f'FINAL/{inning}'
        return_str = f'{status_str} | {away_result} vs. {home_result}'

        await game_channel.send(return_str)
        self.get_current_play.cancel()
      else:
        inning_top_bottom = linescore['inningHalf']
        inning_ordinal = linescore['currentInningOrdinal']
        inning_summation = f'{inning_top_bottom} {inning_ordinal}'

        score_summation = f'{away_team_abbr}: {away_linescore['runs']} {home_team_abbr}: {home_linescore['runs']}'

        overview_str = f'{inning_summation} | {score_summation}'

        current_play = live_data['plays']['currentPlay']

        count = current_play['count']
        pitcher = current_play['matchup']['pitcher']['fullName']
        batter = current_play['matchup']['batter']['fullName']

        pitcher_str = f'P: {pitcher}'
        batter_str = f'AB: {batter}'
        count_str = f'COUNT: {count['balls']}-{count['strikes']}'
        out_str = f'OUTS: {count['outs']}'

        offense = linescore['offense']
        runners_on = []
        if 'first' in offense:
          runners_on.append('1st')
        if 'second' in offense:
          runners_on.append('2nd')
        if 'third' in offense:
          runners_on.append('3rd')

        runners_on_str = f'RUNNERS ON:'

        if len(runners_on) == 0:
          runners_on_str = f'{runners_on_str} NONE'
        else:
          runners_on_str = f'{runners_on_str} {', '.join(runners_on)}'

        play_events = current_play['playEvents']
        if len(play_events) == 0:
          return

        current_play_event = play_events[-1]
        play_details = current_play_event['details']

        if current_play_event['type'] != 'pitch':
          final_str = """
{overview_str}

{description}
----------------
          """.format(overview_str=overview_str,description=play_details['description'])
          await game_channel.send(final_str)
        else:
          play_id = None
          if 'playId' in current_play_event:
            play_id = current_play_event['playId']
          if self.current_play_id != play_id:
            self.current_play_id = play_id


            pitch_data = current_play_event['pitchData']

            current_pitch_str = None
            if 'type' in play_details:
              if play_details['type'] is not None:
                current_pitch_str = f'{pitch_data['startSpeed']} mph {play_details['type']['description']}'
            
            play_str = f'{play_details['description']}'

            result_str = None
            if 'result' in current_play:
              if 'description' in current_play['result']:
                result_str = current_play['result']['description']

            if current_pitch_str is not None:
              play_str = f'{current_pitch_str}; {play_str}'
              if result_str is not None:
                play_str = f'{play_str}\n{result_str}'

            final_str = """
{overview_str}

{pitcher_str} | {batter_str}
{count_str}, {out_str}
{runners_on_str}

{play_str}
----------------
            """.format(overview_str=overview_str, pitcher_str=pitcher_str, batter_str=batter_str, count_str=count_str, out_str=out_str, runners_on_str=runners_on_str, play_str=play_str)

            await game_channel.send(final_str)

  @commands.command(name='live', brief='Subscribes to a live game')
  async def subscribe_to_game(self, ctx: commands.Context, team: str, date: str = None):
    if team is None:
      msg = 'Please provide a team by their common abbreviation to subscribe to a game'
      log(msg, False)
      await ctx.send(msg)
    else:
      game_feed_response = await get_feed_request(team, date)

      if game_feed_response['isOK'] == False:
        log(game_feed_response['msg'], False)
        await ctx.send(game_feed_response['msg'])
      else:
        games = game_feed_response['data']
        number_of_games = len(games)
        game_index = 0

        if number_of_games == 0:
          msg = f'No games found for {team}'
          log(msg, False)
          await ctx.send(msg)
        else:
          game = games[game_index]
          game_suffix = None

          if number_of_games == 2:
            g1_status = games[0]['gameData']['status']['statusCode']
            g2_status = games[1]['gameData']['status']['statusCode']

            if g1_status == 'F' and g2_status == 'F':
              msg = f'Both scheduled games for {team.upper()} are final.'
              log(msg, False)
              await ctx.send(msg)
            else:
              if g1_status == 'F':
                game_index = 1
                game = games[game_index]
                game_suffix = 'g2'
              else:
                game_suffix = 'g1'

          game_data = game['gameData']
          game_status = game_data['status']
          game_datetime = game_data['datetime']

          game_date = game_datetime['officialDate']
          away_team_abbr = game_data['teams']['away']['abbreviation']
          home_team_abbr = game_data['teams']['home']['abbreviation']

          channel_name = f'{away_team_abbr.lower()}_vs_{home_team_abbr.lower()}_{game_date}'
          if game_suffix is not None:
            channel_name = f'{channel_name}_{game_suffix}'

          overwrites = {
            ctx.guild.get_member(self.bot.user.id): discord.PermissionOverwrite(read_messages=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, )
          }
          category = discord.utils.get(ctx.guild.categories, name='dev')

          existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)

          game_channel_msg = None

          if existing_channel is None:
            topic = 'Feed Status: **LIVE**'
            game_channel = await ctx.guild.create_text_channel(name=channel_name, category=category, reason='Live subscription to game', overwrites=overwrites, topic=topic)
            game_channel_msg = f'Created channel at {game_channel.mention} for the {away_team_abbr.upper()} vs. {home_team_abbr.upper()} game'
            if game_suffix is not None:
              created_channel_msg = f'{created_channel_msg} ({game_suffix.upper()})'

            matchup_graphic_response = await get_matchup_graphic_request(team, date)
            if matchup_graphic_response['isOK'] == True:
              matchup_graphic = matchup_graphic_response['data']
              matchup_graphic.seek(0)
              await game_channel.send(file=discord.File(matchup_graphic, f'{channel_name}.png'))
          else:
            game_channel = ctx.guild.get_channel(existing_channel.id)
            game_channel_msg = f'Found existing channel for the {away_team_abbr.upper()} vs. {home_team_abbr.upper()} game: {game_channel.mention}'

          await ctx.send(game_channel_msg)

          if channel_name not in self.running_tasks:
            new_task = None
            if game_status['statusCode'] == 'S' or game_status['statusCode'] == 'P':
              # need to test this out
              game_time_utc = parser.isoparse(game_datetime['dateTime'])
              game_time_utc = game_time_utc.replace(tzinfo=self.from_utc_zone)
              game_time_local_tz = game_time_utc.astimezone(self.to_zone)
              datetime.datetime(hour=game_time_local_tz.hour, minute=game_time_local_tz.minute, tzinfo=self.to_zone)
              start_time = [ datetime.time(hour=game_time_local_tz.hour, minute=game_time_local_tz.minute, tzinfo=self.to_zone) ]
              new_task = tasks.loop(time=start_time)(self.get_current_play)
            else:
              new_task = tasks.loop(seconds=10)(self.get_current_play)
            self.running_tasks[channel_name] = new_task
            new_task.start(ctx=ctx, channel_id=game_channel.id, team=team, game_index=game_index)

  @commands.command(name='unsub', help='Unsubscribes from a game subscription')
  async def unsubscribe_from_live_game(self, ctx: commands.Context, team: str):
    running_tasks_keys = list(self.running_tasks.keys())

    cancel_key = None
    for key in running_tasks_keys:
      if team in key:
        cancel_key = key
        break

    if cancel_key is not None:
      channel = discord.utils.get(ctx.guild.channels, name=cancel_key)
      new_topic = 'Feed Status: Inactive'
      await channel.edit(topic=new_topic)
      self.running_tasks[cancel_key].cancel()
      del self.running_tasks[cancel_key]
      await ctx.send(f'Unsubscribed from game for {team.upper()}')

  @commands.command(name='livelist', help='Shows the live games currently subscribed to')
  async def get_subscribed_games(self, ctx: commands.Context):
    game_keys = list(self.running_tasks.keys())

    if len(game_keys) == 0:
      await ctx.send('No active subscriptions!')
    else:
      mentions = []
      for key in game_keys:
        channel = discord.utils.get(ctx.guild.channels, name=key)
        mentions.append(channel.mention)
      
      channels_str = '\n'.join(mentions)
      await ctx.send(f'Active subscriptions:\n{channels_str}')

async def setup(bot):
  await bot.add_cog(MLB(bot))
