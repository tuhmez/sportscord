from utils.print import pretty_print

def log(msg: str, is_ok: bool):
  okay_header = '[OK]'
  if is_ok is False: okay_header = '[ERR]'
  pretty_print(f'{msg}', okay_header)