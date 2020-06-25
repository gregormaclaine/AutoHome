class Command:
  def __init__(self, name, description=None, function=None):
    self.name = name
    self.description = description
    self.function = function

    self.parent = None

    self.sub_commands = []
  
  def __repr__(self):
    return f"<{'CommandGroup' if self.is_group else 'Command'}: `{self.full_name}`>"
  
  def __call__(self, octrl, *args):
    if len(args) > 0:
      for sub_command in self.sub_commands:
        if sub_command.name == args[0]:
          return sub_command(octrl, *args[1:])
      else:
        return octrl.send(f'Unknown command: `{self.full_name} {args[0]}`')
    if self.function is not None:
      return self.function(octrl, *args)
  
  @property
  def full_name(self):
    if self.parent is None: return self.name
    return f'{self.parent.full_name} {self.name}'

  @property
  def is_group(self):
    return len(self.sub_commands) > 0

  @property
  def full_description(self):
    if not self.is_group: return self.description

    short_description = self.description if self.description is not None else 'A collection of sub-commands'
    max_name_length = max(map(lambda x: len(x.name), self.sub_commands))
    sub_descriptions = [f"{c.name}{(max_name_length - len(c.name)) * ' '}  - {c.description}" for c in self.sub_commands]
    with_prefix = [f"{self.full_name} {desc}" for desc in sub_descriptions]
    return short_description + '\n\nCommands:\n' + '\n  '.join(with_prefix)


def add_command(parent, names, func, to_root=False):
  sub_commands = parent if to_root else parent.sub_commands
  if len(names) == 1:
    for sub_command in sub_commands:
      if sub_command.name == names[0]:
        sub_command.description = func.__doc__
        sub_command.function = func
        return
    else:
      command = Command(names[0], func.__doc__, func)
      command.parent = parent if not to_root else None
      sub_commands.append(command)
  else:
    for sub_command in sub_commands:
      if sub_command.name == names[0]:
        return add_command(sub_command, names[1:], func)
    else:
      command = Command(names[0])
      command.parent = parent if not to_root else None
      sub_commands.append(command)
      add_command(command, names[1:], func)