import os, re, importlib.util

import LogManager
from Module import Module
from ModuleThreadHandler import ModuleThreadHandler, ThreadTask

class ModuleRunner:
  MAX_THREADS = 3

  def __init__(self, parent):
    self.parent = parent
    self.logger = LogManager.create_logger('MODULES')

    self.closing = False

    self.thread_handler = ModuleThreadHandler(self.logger)

    self.logger.info('Initialising modules...')
    self.get_modules()

    self.logger.info(f"Currently running {len(self.modules)} module{'s' if len(self.modules) != 1 else ''}...")
  
  def close(self):
    self.thread_handler.close()
    self.closing = True
  
  def get_modules(self):
    self.modules = []
    self.bad_modules = []

    # Get possible files that could contain a module
    module_filenames = []
    x = '/' if os.path.sep == '/' else r'\\'
    pattern = re.compile(f'^.{x}modules{x}[^{x}]+$')
    for subdir, _, files in os.walk(os.path.join(os.curdir, 'modules')):
      if pattern.match(subdir):
        if 'main.py' in files:
          module_filenames.append(os.path.join(subdir, 'main.py'))
        else:
          self.bad_modules.append((subdir.split(os.path.sep)[-1], 'No main.py file'))

    # Go through files and try to import a class
    for filename in module_filenames:
      spec = importlib.util.spec_from_file_location(filename[2:-3].replace(os.path.sep, '.'), filename)
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      if not hasattr(module, 'export'):
        self.bad_modules.append((filename.split(os.path.sep)[-2], 'No exported class in main.py'))
      elif not Module.is_valid(module.export):
        self.bad_modules.append((filename.split(os.path.sep)[-2], 'Exported module is invalid'))
      else:
        self.init_module(module.export)
    
    for module_name, reason in self.bad_modules:
      self.logger.warning(f'Installed module `{module_name}` cannot be loaded: {reason}')

  def run_modules(self, minutes_past):
    for module in [m for m in self.modules if m.should_occur(minutes_past)]:
      self.run_module(module)

  def run_module(self, module):
    self.thread_handler.add_task(module, ThreadTask.RUN)
  
  def init_module(self, base_class):
    module = Module(self, base_class)
    self.thread_handler.add_task(module, ThreadTask.INIT, -1)
    self.modules.append(module)
