from TelnetServerCommand import Command, add_command
from Module import ModuleStatus

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

  return '\n\r'.join(formatted_rows)

commands = []
def command(*names):
  def decorator_command(func):
    add_command(commands, names, func, True)
    return func
  return decorator_command

@command('help')
def help(octrl, *args):
  """Gives a brief description of all commands"""
  if len(args) == 0:
    max_length = max(map(lambda x: len(x.name), commands))
    for command in commands:
      octrl.send(f"{command.name}{(max_length - len(command.name)) * ' '}  - {command.description}\n\r")
  else:
    for command in commands:
      if command.name == args[0]:
        return octrl.send(command.help(args[1:]) + '\n\r')
    else:
      octrl.send(f"Unknown command: `{args[0]}`")

@command('shutdown')
def shutdown(octrl, *args):
  """Closes AutoHome server application"""
  if octrl.confirm():
    octrl.server.parent.close_server()

@command('quit')
def quit(octrl, *args):
  """Closes current server connection"""
  pass

@command('telnet', 'list')
def list_connections(octrl, *args):
  """Lists all previous telnet connections"""
  octrl.send(octrl.stats.d_connections.replace('\n', '\n\r') + '\n\r')

@command('modules')
def modules(octrl, *args):
  """Read & manipulate the installed modules on the server"""
  pass

@command('modules', 'list')
def list_modules(octrl, *args):
  """Lists all modules found and their status"""
  octrl.send(octrl.stats.d_all_modules.replace('\n', '\n\r') + '\n\r')

def change_module_status(octrl, index, status):
  try:
    module = octrl.server.parent.mr.modules[int(index) - 1]
  except ValueError:
    return octrl.send(f'Error: `{index}` is not an integer index\n\r')
  except IndexError:
    return octrl.send(f'Error: Index out of range\n\r')

  octrl.server.logger.info(f"Module `{module.name}` status now set to: {status}")
  module.status = status
  octrl.send(f"Module `{module.name}` is now {'running' if status == ModuleStatus.RUNNING else 'paused'}\n\r")

@command('modules', 'start')
def start_module(octrl, index, *args):
  """Starts a paused module (Takes the module index)"""
  change_module_status(octrl, index, ModuleStatus.RUNNING)

@command('modules', 'pause')
def pause_module(octrl, index, *args):
  """Pauses a running module (Takes the module index)"""
  change_module_status(octrl, index, ModuleStatus.PAUSED)

@command('modules', 'run')
def run_module(octrl, index, *args):
  """Run a certain module once independantly of clock"""
  try:
    module = octrl.server.parent.mr.modules[int(index) - 1]
  except ValueError:
    return octrl.send(f'Error: `{index}` is not an integer index\n\r')
  except IndexError:
    return octrl.send(f'Error: Index out of range\n\r')

  octrl.server.logger.info(f'Attempting to run module `{module.name}`...')
  octrl.send(f'Attempting to run module `{module.name}`...')
  octrl.server.parent.mr.run_module(module)

class TelnetServerOutputController:
  def __init__(self, server):
    self.server = server
    self.send = server.send
    self.confirm = server.confirm
    self.prompt = server.prompt
    self.stats = server.parent.stats

  def handle_command(self, line):
    command, *args = line.split(' ')
    for c in commands:
      if c.name == command:
        return c(self, *args)
    else:
      self.send(f"Unknown command: `{command}`")
