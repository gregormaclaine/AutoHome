from TelnetServerCommand import Command, add_command

commands = []

def command(*names):
  def decorator_command(func):
    add_command(commands, names, func, True)
    return func
  return decorator_command

@command('help')
def help(octrl):
  """Gives a brief description of all commands"""
  max_length = max(map(lambda x: len(x.name), commands))
  for command in commands:
    octrl.send(f"{command.name}{(max_length - len(command.name)) * ' '}  - {command.description}\n\r")

@command('shutdown')
def shutdown(octrl):
  """Closes AutoHome server application"""
  if octrl.confirm():
    octrl.server.parent.close_server()

@command('quit')
def quit(octrl):
  """Closes current server connection"""
  pass

@command('modules', 'list')
def list_modules(octrl):
  """Lists the all modules found and their status"""
  modules = octrl.server.parent.modules
  bad_modules = octrl.server.parent.bad_modules

  if len(modules) == 0 and len(bad_modules) == 0:
    return octrl.send('There are no installed modules\n')

  one = len(modules) == 1
  octrl.send(f"There {'is' if one else 'are'} {len(modules) if len(modules) > 0 else 'no'} valid module{'' if one else 's'} installed:\n\r")
  if len(modules) > 0:
    max_module_length = max(map(lambda x: len(x.__class__.NAME), modules))
    for m in modules:
      name = m.__class__.NAME
      octrl.send(f"\t{name}{(max_module_length - len(name)) * ' '}  | Currently running...\n\r")
  
  if len(bad_modules) > 0:
    one = len(bad_modules) == 1
    octrl.send(f"\nThere {'is' if one else 'are'} {len(bad_modules)} invalid folder{'' if one else 's'} in the modules directory:\n\r")
    max_bad_module_length = max(map(lambda x: len(x[0]), bad_modules))
    for folder, reason in bad_modules:
      octrl.send(f"\t{folder}{(max_bad_module_length - len(folder)) * ' '}  | {reason}\n\r")

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
