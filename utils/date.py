from datetime import date, timedelta

def get_datetime(requested_date, format):
  month = 0
  day = 0
  year = 0

  today = date.today()
  if requested_date == 'yesterday':
    yesterday = today - timedelta(days=1)
    month = yesterday.month
    day = yesterday.day
    year = yesterday.year
  elif requested_date == 'tomorrow':
    tomorrow = today + timedelta(days=1)
    month = tomorrow.month
    day = tomorrow.day
    year = tomorrow.year
  elif requested_date == 'today':
    month = today.month
    day = today.day
    year = today.year
  else:
    date_string_arr = requested_date.split('/')
    month = date_string_arr[0]
    day = date_string_arr[1]
    year = date_string_arr[2]

  if format == 'json': return { 'month': month, 'day': day, 'year': year }
  else: return mdy_to_slash_date(month, day, year)

def mdy_to_slash_date(month: str, day: str, year: str):
  return f'{month}/{day}/{year}'