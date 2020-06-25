from TelnetServerCommand import Command, add_command
from Module import ModuleStatus

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
  modules = octrl.server.parent.modules
  bad_modules = octrl.server.parent.bad_modules

  if len(modules) == 0 and len(bad_modules) == 0:
    return octrl.send('There are no installed modules\n')

  one = len(modules) == 1
  octrl.send(f"There {'is' if one else 'are'} {len(modules) if len(modules) > 0 else 'no'} valid module{'' if one else 's'} installed:\n\n\r")
  if len(modules) > 0:
    max_module_length = max(map(lambda x: len(x.base_class.NAME), modules))
    for i, m in enumerate(modules):
      num = str(i+1).zfill(2 if len(modules) > 9 else 1)
      name = m.base_class.NAME
      octrl.send(f"  ({num}) {name}{(max_module_length - len(name)) * ' '}  | {m.status}\n\r")
  
  if len(bad_modules) > 0:
    one = len(bad_modules) == 1
    octrl.send(f"\nThere {'is' if one else 'are'} {len(bad_modules)} invalid folder{'' if one else 's'} in the modules directory:\n\n\r")
    max_bad_module_length = max(map(lambda x: len(x[0]), bad_modules))
    for folder, reason in bad_modules:
      octrl.send(f"  {folder}{(max_bad_module_length - len(folder)) * ' '}  | {reason}\n\r")

def change_module_status(octrl, index, status):
  try:
    index = int(index) - 1
  except ValueError:
    return octrl.send(f'Error: `{index}` is not an integer index\n\r')

  modules = octrl.server.parent.modules
  if index >= len(modules):
    return octrl.send(f'Error: Index out of range\n\r')
  module = octrl.server.parent.modules[index]

  octrl.server.logger.info(f"Module `{modules.base_class_NAME}` status now set to: {status}")
  module.status = status
  octrl.send(f"Module `{module.base_class.NAME}` is now {'running' if status == ModuleStatus.RUNNING else 'paused'}\n\r")

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
    index = int(index) - 1
  except ValueError:
    return octrl.send(f'Error: `{index}` is not an integer index\n\r')

  modules = octrl.server.parent.modules
  if index >= len(modules):
    return octrl.send(f'Error: Index out of range\n\r')
  module = octrl.server.parent.modules[index]

  octrl.server.logger.info(f'Adding module `{module.base_class.NAME}` to queue...')
  octrl.server.parent.queue.put(module)
  octrl.send(f'Module `{module.base_class.NAME}` added to queue')

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
