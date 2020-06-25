class Command:
  def __init__(self, name, description, function):
    self.name = name
    self.description = description
    self.function = function

  def __repr__(self):
    return f'<Command: `{self.name}`>'

def command(name):
  def decorator_command(func):
    func.command = Command(name, func.__doc__, func)
    return func
  return decorator_command

class TelnetServerOutputController:
  def __init__(self, server):
    self.server = server
    self.send = server.send
    self.confirm = server.confirm
    self.prompt = server.prompt

    self.commands = []
    self.get_commands()
  
  def handle_command(self, line):
    command, *args = line.split(' ')
    for c in self.commands:
      if c.name == command:
        return c.function(self, *args)
    else:
      self.send(f"Unknown command: `{command}`")
  
  def get_commands(self):
    self.commands = []
    for name in dir(self):
      attribute = getattr(self, name)
      if hasattr(attribute, 'command'):
        self.commands.append(getattr(attribute, 'command'))

  @command('help')
  def help(self):
    """Gives a brief description of all commands"""
    max_length = max(map(lambda x: len(x.name), self.commands))
    for command in self.commands:
      self.send(f"{command.name}{(max_length - len(command.name)) * ' '}  - {command.description}\n\r")
  
  @command('shutdown')
  def shutdown(self):
    """Closes AutoHome server application"""
    if self.confirm():
      self.server.parent.close_server()
  
  @command('quit')
  def quit(self):
    """Closes current server connection"""
    pass

  @command('modules')
  def modules(self, arg1='list'):
    if arg1 == 'list':
      modules = self.server.parent.modules
      bad_modules = self.server.parent.bad_modules

      if len(modules) == 0 and len(bad_modules) == 0:
        return self.send('There are no installed modules\n')

      one = len(modules) == 1
      self.send(f"There {'is' if one else 'are'} {len(modules) if len(modules) > 0 else 'no'} valid module{'' if one else 's'} installed:\n\r")
      if len(modules) > 0:
        max_module_length = max(map(lambda x: len(x.__class__.NAME), modules))
        for m in modules:
          name = m.__class__.NAME
          self.send(f"\t{name}{(max_module_length - len(name)) * ' '}  | Currently running...\n\r")
      
      if len(bad_modules) > 0:
        one = len(bad_modules) == 1
        self.send(f"\nThere {'is' if one else 'are'} {len(bad_modules)} invalid folder{'' if one else 's'} in the modules directory:\n\r")
        max_bad_module_length = max(map(lambda x: len(x[0]), bad_modules))
        for folder, reason in bad_modules:
          self.send(f"\t{folder}{(max_bad_module_length - len(folder)) * ' '}  | {reason}\n\r")

