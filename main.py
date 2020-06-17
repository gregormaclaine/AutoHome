import time, sys, os, re, importlib.util
import logging
from queue import Queue

from PhoneNotifications import Notifier
from ModuleRunner import ModuleRunner

def applyPadding(name, num=15):
  extra = num - len(name)
  return f"{' ' * (extra // 2 + extra % 2)}{name}{' ' * (extra // 2)}"

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s [%(name)-15s | %(levelname)-8s]: %(message)s',
  datefmt='%d-%m-%y %H:%M:%S',
  filename='logs/current.log'
)

master_logger = logging.getLogger(applyPadding('MASTER'))
master_logger.addHandler(logging.StreamHandler())

testing_mode = len(sys.argv) > 1 and sys.argv[1] == 'test'

def is_module_valid(module):
  return hasattr(module, 'OCCUR_EVERY') and \
    hasattr(module, 'run') and hasattr(module, 'NAME')

def initialise_module(module_class):
  logger = logging.getLogger(applyPadding(module_class.NAME))
  logger.addHandler(logging.StreamHandler())
  return module_class(
    logger=logger,
    notifications=Notifier
  )

def get_modules():
  pattern = re.compile(r'^.\\modules\\[^\\]+$')
  module_filenames = []
  for subdir, _, files in os.walk(os.path.join(os.curdir, 'modules')):
    if pattern.match(subdir) and 'main.py' in files:
      module_filenames.append(os.path.join(subdir, 'main.py'))

  master_logger.info('Initialising modules...')
  modules = []
  for filename in module_filenames:
    spec = importlib.util.spec_from_file_location(filename[2:-3].replace('\\', '.'), filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, 'export') and is_module_valid(module.export):
      modules.append(initialise_module(module.export))
    
  return modules

def close_server(mr):
  master_logger.info('Closing Autohome server...')
  mr.stop_workers()

if __name__ == "__main__":
  master_logger.info('Initialising AutoHome server...')
  queue = Queue()
  mr = ModuleRunner(master_logger, queue)

  minutes_past = 0.0
  modules = get_modules()
  master_logger.info(f"Currently running {len(modules)} module{'s' if len(modules) != 1 else ''}...")

  try:
    while True:
      mr.fill_workers()

      for module in modules:
        if minutes_past % module.OCCUR_EVERY == 0:
          queue.put(module)

      if testing_mode:
        input('Press enter to pass 30 seconds...')
      else:
        print('Waiting 30 seconds...')
        time.sleep(30)
      minutes_past += 0.5
  except KeyboardInterrupt:
    close_server(mr)
  except Exception:
    master_logger.critical(f'An error has occured running the AutoHome server...', exc_info=True)
    close_server(mr)
