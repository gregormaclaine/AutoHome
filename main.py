import time, sys, os, re, importlib.util
import logging
from queue import Queue

from Module import Module, ModuleStatus
from ModuleRunner import ModuleRunner
from TelnetServer import TelnetServer

import Logging
Logging.init()

def applyPadding(name, num=15):
  extra = num - len(name)
  return f"{' ' * (extra // 2 + extra % 2)}{name}{' ' * (extra // 2)}"

testing_mode = len(sys.argv) > 1 and sys.argv[1] == 'test'

class Main:
  def __init__(self):
    self.logger = Logging.create_logger('MASTER')

    self.closing = False

    self.logger.info('Initialising AutoHome server...')
    self.queue = Queue()
    self.mr = ModuleRunner(self)
    self.server = TelnetServer(self)

    self.modules = []
    self.bad_modules = []
    self.get_modules()
    self.logger.info(f"Currently running {len(self.modules)} module{'s' if len(self.modules) != 1 else ''}...")

    self.mainloop()

  def get_modules(self):
    x = '/' if os.path.sep == '/' else r'\\'
    pattern = re.compile(f'^.{x}modules{x}[^{x}]+$')
    module_filenames = []
    for subdir, _, files in os.walk(os.path.join(os.curdir, 'modules')):
      if pattern.match(subdir):
        if 'main.py' in files:
          module_filenames.append(os.path.join(subdir, 'main.py'))
        else:
          self.bad_modules.append((subdir.split(os.path.sep)[-1], 'No main.py file'))

    self.logger.info('Initialising modules...')
    self.modules = []
    for filename in module_filenames:
      spec = importlib.util.spec_from_file_location(filename[2:-3].replace(os.path.sep, '.'), filename)
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      if not hasattr(module, 'export'):
        self.bad_modules.append((filename.split(os.path.sep)[-2], 'No exported class in main.py'))
      elif not Module.is_valid(module.export):
        self.bad_modules.append((filename.split(os.path.sep)[-2], 'Exported module is invalid'))
      else:
        self.modules.append(Module(module.export, Logging.create_logger(module.export.NAME)))
    
    for module_name, reason in self.bad_modules:
      self.logger.warning(f'Installed module `{module_name}` cannot be loaded: {reason}')
      
  def close_server(self):
    self.logger.info('Closing Autohome server...')
    self.server.close()
    self.mr.stop_workers()
    self.closing = True
    exit()
  
  def mainloop(self):
    minutes_past = 0.0
    try:
      while True:
        if self.closing: break
        self.mr.fill_workers()

        for module in self.modules:
          if module.status == ModuleStatus.RUNNING and minutes_past % module.base_class.OCCUR_EVERY == 0:
            self.queue.put(module)

        if testing_mode:
          input('Press enter to pass 30 seconds...')
        else:
          print('Waiting 30 seconds...')
          for _ in range(30):
            time.sleep(1)
            if self.closing: break
        minutes_past += 0.5
    except KeyboardInterrupt:
      self.close_server()
    except Exception:
      self.logger.critical(f'An error has occured running the AutoHome server...', exc_info=True)
      self.close_server()

if __name__ == "__main__":
  Main()