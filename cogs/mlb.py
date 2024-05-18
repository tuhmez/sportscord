import discord
from discord.ext import commands
import datetime
from dateutil import parser, tz

from urls.mlb import boxscore_url, logo_url, ext_gameday_url
from utils.mlb import  get_player_stats, get_probable_statline
from utils.logger import log
from utils.date import get_datetime

from help.mlb import games_long_help, magic_long_help, matchup_long_help, probables_long_help, record_long_help, score_long_help

from workers.mlb import get_game_request, get_games_request, get_logo_request, get_magic_number_request, get_matchup_graphic_request, get_player_stats_request, get_probables_request, get_record_request, get_score_request, get_team_request

class MLB(commands.Cog, name='mlb', command_attrs=dict(hidden=False)):
  def __init__(self, bot):
    self.bot = bot
    self.from_utc_zone = tz.tzutc()
    self.to_zone = tz.tzlocal()

  @commands.command(name='logo', brief='Get a logo for an MLB team')
  async def get_logo(self, ctx, team: str):
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
  async def get_score(self, ctx, team: str, date: str = None):
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
  async def get_record(self, ctx, team: str, date: str = None):
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

        if jdata['divisionRank'] == '1':
          div_place = f'1st in {division}'
        elif jdata['divisionRank'] == '2':
          div_place = f'2nd in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'
        elif jdata['divisionRank'] == '3':
          div_place = f'3rd in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'
        elif jdata['divisionRank'] == '4':
          div_place = f'4th in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'
        else:
          div_place = f'5th in {division}'
          if divisionGamesBack != '-':
            div_place = f'{div_place} ({divisionGamesBack} GB)'

        standings_str = f'{team.upper()}: {jdata["wins"]}-{jdata["losses"]}, {div_place}'
        await ctx.send(standings_str)
  
  @commands.command(name='magic', brief='Gets the magic number for a team', help=magic_long_help)
  async def get_magic_number(self, ctx, team: str, year: str = None):
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
          if away_pitcher is not None:
            away_response = await get_player_stats_request(away_pitcher)

            if away_response['isOK'] == False:
              log(away_response['msg'], False)
              await ctx.send(away_response['msg'])
            else:
              away_jdata = away_response['data']
              away_pitcher_stats = get_player_stats(away_jdata['people'][0]['stats'], 'yearByYear')
              for j in away_pitcher_stats['splits']:
                if j['season'] == current_year['year']: current_away_pitcher_data = j; break
              if away_pitcher_stats == None:
                msg = f'Could not pitcher stats for {team.upper()}'
                log(f'{msg} - CMD (probables)', True)
                await ctx.send(msg)
          
          current_home_pitcher_data = None
          home_jdata = None
          if home_pitcher is not None:
            home_response = await get_player_stats_request(home_pitcher)
            if home_response['isOK'] == False:
              log(home_response['msg'], False)
              await ctx.send(home_response['msg'])
            else:
              home_jdata = home_response['data']
              home_pitcher_stats = get_player_stats(home_jdata['people'][0]['stats'], 'yearByYear')
              for j in home_pitcher_stats['splits']:
                if j['season'] == current_year['year']: current_home_pitcher_data = j; break
              if home_pitcher_stats == None:
                msg = f'Could not pitcher stats for {team.upper()}'
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
  async def get_games(self, ctx, date: str = None):
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
  async def get_matchup(self, ctx, team: str, date: str = None):
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

async def setup(bot):
  await bot.add_cog(MLB(bot))