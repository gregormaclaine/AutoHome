import time, sys, os, re, importlib.util, traceback
import logging
from threading import Thread
from queue import Queue

from PhoneNotifications import Notifier

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

testing_mode = len(sys.argv) > 1 and sys.argv[1] == 'test'

NUM_TASK_THREADS = 1

def complete_queue_tasks(queue):
  while True:
    module = queue.get()
    master_logger.info(f'Running module: {module.NAME}')
    try:
      module.run()
    except:
      master_logger.error(f'There was an error running module: {module.NAME}', exc_info=True)

def is_module_valid(module):
  return hasattr(module, 'OCCUR_EVERY') and \
    hasattr(module, 'run') and hasattr(module, 'NAME')

def initialise_module(module_class):
  return module_class(
    logger=logging.getLogger(applyPadding(module_class.NAME)),
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

if __name__ == "__main__":
  master_logger.info('Initialising AutoHome server...')
  queue = Queue()

  for _ in range(NUM_TASK_THREADS):
    worker = Thread(target=complete_queue_tasks, args=(queue,))
    worker.start()

  minutes_past = 0.0
  modules = get_modules()
  master_logger.info(f"Currently running {len(modules)} module{'s' if len(modules) != 1 else ''}...")
  while True:

    for module in modules:
      if minutes_past % module.OCCUR_EVERY == 0:
        queue.put(module)

    if testing_mode:
      input('Press enter to pass 30 seconds...')
    else:
      print('Waiting 30 seconds...')
      time.sleep(30)
    minutes_past += 0.5
