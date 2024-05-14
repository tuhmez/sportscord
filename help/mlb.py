score_long_help = """
-score <input_team> [date]

Returns a score based on an input team, where an input team is required, but input date is not.
If no date is specified, it will default to today's date.

<input_team> - Must be team abbreviation; ex. MIL (case-insensitive)

[date] - Optional, accepts a date in mm/dd/yyyy format (ex. 10/1/2018) or keywords 'yesterday', 'today', or 'tomorrow'

Examples:

-score nyy
-score atl yesterday
-score mil 10/1/2018
"""

record_long_help = """
-record <input_team> [year]

Returns the win/loss record for an input team, where an input team is required, but input year is not.
If no year is specified, it will default to the current year.

<input_team> - Must be team abbreviation; ex. MIL (case-insensitive)

[year] - Optional, must be in yyyy format (ex. 2022)

Examples:

-record mil
-record sea 2001
"""

magic_long_help = """
-magic <input_team> [year]

Returns the either the magic number or the elimination numbers for an input team, where an input team is required, but input year is not.
If no year is specified, it will default to the current year

<input_team> - Must be team abbreviation; ex. MIL (case-insensitive)

[year] - Optional, must be in yyyy format (ex. 2022)

Examples:

-magic mil
-magic mil 2018
"""

probables_long_help = """
-probables <input_team> [date]

Returns the probable pitchers for an input team, where an input team is required, but input date is not.
If no date is specified, it will default to the current day.

<input_team> - Must be team abbreviation; ex. MIL (case-insensitive)

[date] - Optional, accepts a date in mm/dd/yyyy format (ex. 10/1/2018) or keywords 'yesterday', 'today', or 'tomorrow'

Examples:

-probables mil
-probables bos tomorrow
"""

games_long_help = """
-games [date]

Returns the complete slate of games; input date is not required. If no date is specified, it will default to the current day.

[date] - Optional, accepts a date in mm/dd/yyyy format (ex. 10/1/2018) or keywords 'yesterday', 'today', or 'tomorrow'

Examples:

-games
-games yesterday
"""

matchup_long_help = """
-matchup <input_team> [date]

Returns the matchup for the desired team which includes game graphic and details like probables, lineup (if available), record; input date is not required. If no date is specified, it will default to the current date.

<input_team> - Must be team abbreviation; ex. MIL (case-insensitive)

[date] - Optional, accepts a date in mm/dd/yyyy format (ex. 10/1/2018) or keywords 'yesterday', 'today', or 'tomorrow'

Examples:
-matchup mil
-matchup chc 10/1/2018
"""
