import time, sys, os, re, importlib.util
import logging
from queue import Queue

from PhoneNotifications import Notifier
from ModuleRunner import ModuleRunner
from TelnetServer import TelnetServer

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s [%(name)-15s | %(levelname)-8s]: %(message)s',
  datefmt='%d-%m-%y %H:%M:%S',
  filename='logs/current.log'
)

def applyPadding(name, num=15):
  extra = num - len(name)
  return f"{' ' * (extra // 2 + extra % 2)}{name}{' ' * (extra // 2)}"

testing_mode = len(sys.argv) > 1 and sys.argv[1] == 'test'

class Main:
  def __init__(self):
    self.logger = logging.getLogger(applyPadding('MASTER'))
    self.logger.addHandler(logging.StreamHandler())

    self.closing = False

    self.logger.info('Initialising AutoHome server...')
    self.queue = Queue()
    self.mr = ModuleRunner(self)
    self.server = TelnetServer(self, self.mr)

    self.modules = []
    self.get_modules()
    self.logger.info(f"Currently running {len(self.modules)} module{'s' if len(self.modules) != 1 else ''}...")

    self.mainloop()

  @staticmethod
  def is_module_valid(module):
    return hasattr(module, 'OCCUR_EVERY') and \
      hasattr(module, 'run') and hasattr(module, 'NAME')

  @staticmethod
  def create_logger(name):
    logger = logging.getLogger(applyPadding(name.upper()))
    logger.addHandler(logging.StreamHandler())
    return logger

  @staticmethod
  def initialise_module(module_class):
    return module_class(
      logger=Main.create_logger(module_class.NAME),
      notifications=Notifier
    )

  def get_modules(self):
    pattern = re.compile(r'^.\\modules\\[^\\]+$')
    module_filenames = []
    for subdir, _, files in os.walk(os.path.join(os.curdir, 'modules')):
      if pattern.match(subdir) and 'main.py' in files:
        module_filenames.append(os.path.join(subdir, 'main.py'))

    self.logger.info('Initialising modules...')
    self.modules = []
    for filename in module_filenames:
      spec = importlib.util.spec_from_file_location(filename[2:-3].replace('\\', '.'), filename)
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      if hasattr(module, 'export') and Main.is_module_valid(module.export):
        self.modules.append(Main.initialise_module(module.export))
      
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
          if minutes_past % module.OCCUR_EVERY == 0:
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