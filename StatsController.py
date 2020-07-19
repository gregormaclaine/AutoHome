from datetime import datetime

class TelnetConnectionRecord:
  def __init__(self, address):
    self.address = address
    self.start = datetime.now()
    self.end = None
  
  def end_connection(self):
    self.end = datetime.now()
  
  @property
  def is_open(self):
    return self.end == None
  
  @property
  def length(self):
    return self.end - self.start

class Stats:
  """An object to keep track of statistics regarding the current running of the program"""
  def __init__(self, main):
    self.modules = main.mr.modules
    self.bad_modules = main.mr.bad_modules

    self.connections = []

class StatsRecorder(Stats):
  """The Stats object but with functions to aid manipulating / adding to the records"""
  def record_connection(self, address):
    conn_record = TelnetConnectionRecord(address)
    self.connections.append(conn_record)
    return conn_record.end_connection

class StatsDecorator(Stats):
  """A Stats object with decorated data fit for looking at visually"""
  @property
  def d_all_modules(self):
    return self.d_modules + f'\n\n{self.d_bad_modules}' if len(self.bad_modules) > 0 else ''

  @property
  def d_modules(self):
    if len(self.modules) == 0: return 'There are no valid modules installed.'

    one = len(self.modules) == 1
    top_line = f"There {'is' if one else 'are'} {len(self.modules)} valid module{'' if one else 's'} installed:"
    columns = self.format_columns('  (_) _  | _ | _ |', enumerate(self.modules),
      lambda r: r[0] + 1, lambda r: r[1].name, lambda r: r[1].status, lambda r: r[1].time_since_last_run)
    
    return top_line + '\n\n' + columns
  
  @property
  def d_bad_modules(self):
    if len(self.modules) == 0: return 'No invalid modules could be found.'

    one = len(self.bad_modules) == 1
    top_line = f"There {'is' if one else 'are'} {len(self.bad_modules)} invalid folder{'' if one else 's'} in the modules directory:"
    columns = self.format_columns('  _  | _', self.bad_modules, lambda r: r[0], lambda r: r[1])
    return top_line + '\n\n' + columns
  
  @property
  def d_connections(self):
    if len(self.connections) == 0: return 'No connections have been recorded yet...'

    one = len(self.connections) == 1
    top_line = f"There {'has' if one else 'have'} been {len(self.connections)} telnet connection{'' if one else 's'} so far:"
    columns = self.format_columns('  _  | _  | _', reversed(self.connections),
      lambda r: r.address, lambda r: self.format_timedelta(datetime.now() - r.start) + ' ago', lambda r: (self.format_timedelta(r.length) + ' long') if not r.is_open else 'Currently open...')
    return top_line + '\n\n' + columns
    
  @staticmethod
  def format_columns(strf, rows, *getters):
    rows = list(rows)
    if len(getters) != strf.count('_'):
      raise Exception('Number of columns does not match number of getters')

    strf_parts = strf.split('_')
    max_lengths = [max(map(lambda row: len(str(getter(row))), rows)) for getter in getters]

    formatted_rows = []
    for row in rows:
      column_values = [str(getter(row)) for getter in getters]
      spaced_values = [v + (max_lengths[i] - len(v)) * ' ' for i, v in enumerate(column_values)]
      row_line = ''.join([a + b for a, b in zip(strf_parts, spaced_values)]) + strf_parts[-1]
      formatted_rows.append(row_line)
    
    return '\n'.join(formatted_rows)
  
  @staticmethod
  def format_timedelta(td):
    s = td.seconds
    if s > 60 * 60 * 24 * 2:
      return 'Multiple days'

    if s < 60:            num, msmt = s, 'second'
    elif s < 60 * 60 * 2: num, msmt = s // 60, 'minute'
    else:                 num, msmt = s // (60 * 60), 'hour'
    
    return f"{num} {msmt}{'' if num == 1 else 's'}"

class StatsController(StatsRecorder, StatsDecorator):
  pass
