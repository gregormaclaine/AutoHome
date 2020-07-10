from threading import Thread
import os, re, importlib.util, time
from queue import Queue

import LogManager
from Module import Module

class ModuleRunner:
  MAX_THREADS = 3

  def __init__(self, parent):
    self.parent = parent
    self.logger = LogManager.create_logger('MODULES')

    self.closing = False

    self.backlog = Queue()
    self.backlog_thread = None

    self.logger.info('Initialising modules...')
    self.get_modules()

    self.logger.info(f"Currently running {len(self.modules)} module{'s' if len(self.modules) != 1 else ''}...")
  
  def close(self):
    self.closing = True
  
  @property
  def can_start_new_thread(self):
    return len([m for m in self.modules if m.thread != None]) < ModuleRunner.MAX_THREADS

  def start_backlog(self):
    if self.backlog_thread != None or self.backlog.empty(): return
    self.logger.info('Starting backlog thread...')
    self.backlog_thread = Thread(target=self.clear_backlog, name='Module-Backlog-Thread')
    self.backlog_thread.start()

  def clear_backlog(self):
    while not self.backlog.empty() and not self.closing:
      if not self.can_start_new_thread:
        time.sleep(0.5)
        continue
      module = self.backlog.get()
      module()
    
    self.logger.info(f"{'' if self.closing else 'Module backlog is empty. '}Stopping backlog thread...")
    self.backlog_thread = None
  
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
        self.modules.append(Module(self, module.export))
    
    for module_name, reason in self.bad_modules:
      self.logger.warning(f'Installed module `{module_name}` cannot be loaded: {reason}')

  def run_modules(self, minutes_past):
    for module in [m for m in self.modules if m.should_occur(minutes_past)]:
      self.run_module(module)

  def run_module(self, module):
    if self.can_start_new_thread:
      module()
    else:
      self.logger.warning(f'Max module threads reached. Adding `{module.name}` to backlog...')
      self.backlog.put(module)
      self.start_backlog()
