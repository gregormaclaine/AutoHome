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

    self.commands = []
    self.get_commands()
  
  def handle_command(self, line):
    command, *args = line.split(' ')
    for c in self.commands:
      if c.name == command:
        return c.function(self, *args)
    else:
      self.server.send(f"Unknown command: `{command}`")
  
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
      self.server.send(f"{command.name}{(max_length - len(command.name)) * ' '}  - {command.description}\n\r")
  
  @command('shutdown')
  def shutdown(self):
    """Closes AutoHome server application"""
    if self.server.confirm():
      self.server.parent.close_server()
  
  @command('quit')
  def quit(self):
    """Closes current server connection"""
    pass
