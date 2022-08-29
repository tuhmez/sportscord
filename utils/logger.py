def log(msg: str, is_ok: bool):
  okay_header = '[OK]'
  if is_ok is False: okay_header = '[ERR]'
  print(f'{okay_header} - {msg}')