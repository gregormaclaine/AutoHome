from TelnetServerCommand import Command, add_command
from Module import ModuleStatus

def format_columns(strf, rows, *getters):
  rows = list(rows)
  if len(getters) != strf.count('_'):
    raise Exception('Number of columns does not match number of getters')

  max_lengths = [max(map(lambda row: len(str(getter(row))), rows)) for getter in getters]

  formatted_rows = [strf for _ in rows]
  for row_num, row in enumerate(rows):
    for i, getter in enumerate(getters):
      s = str(getter(row)) + (max_lengths[i] - len(str(getter(row)))) * ' '
      formatted_rows[row_num] = formatted_rows[row_num].replace('_', s, 1)
  
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

@command('modules')
def modules(octrl, *args):
  """Read & manipulate the installed modules on the server"""
  pass

@command('modules', 'list')
def list_modules(octrl, *args):
  """Lists the all modules found and their status"""
  modules = octrl.server.parent.mr.modules
  bad_modules = octrl.server.parent.mr.bad_modules

  if len(modules) == 0 and len(bad_modules) == 0:
    return octrl.send('There are no installed modules\n')

  one = len(modules) == 1
  octrl.send(f"There {'is' if one else 'are'} {len(modules) if len(modules) > 0 else 'no'} valid module{'' if one else 's'} installed:\n\n\r")
  if len(modules) > 0:    
    s = format_columns('  (_) _  | _ | _ |', enumerate(modules),
      lambda r: r[0] + 1, lambda r: r[1].name, lambda r: r[1].status, lambda r: r[1].time_since_last_run)
    octrl.send(s + '\n\r')
  
  if len(bad_modules) > 0:
    one = len(bad_modules) == 1
    octrl.send(f"\nThere {'is' if one else 'are'} {len(bad_modules)} invalid folder{'' if one else 's'} in the modules directory:\n\n\r")
    s = format_columns('  _  | _', bad_modules,
      lambda r: r[0], lambda r: r[1])
    octrl.send(s + '\n\r')

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

  def handle_command(self, line):
    command, *args = line.split(' ')
    for c in commands:
      if c.name == command:
        return c(self, *args)
    else:
      self.send(f"Unknown command: `{command}`")
