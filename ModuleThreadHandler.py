from threading import Thread
from queue import Queue
import time

class ThreadTask:
  INIT = 'Initialise'
  RUN = 'Run the module'

class ModuleThreadHandler:
  MAX_MODULE_THREADS = 3

  def __init__(self, logger):
    self.logger = logger

    self.queues = []
    self.modules_in_use = []
    self.threads = [None for _ in range(self.MAX_MODULE_THREADS)]

    self.thread_filler = None

    self.closing = False
  
  def close(self):
    self.closing = True
  
  def new_thread_slot(self):
    try:
      return self.threads.index(None)
    except ValueError:
      return None

  def add_task(self, module, task, priority=0):
    queue = Queue()
    if task == ThreadTask.RUN and module.module is None:
      queue.put((module, ThreadTask.INIT))
    queue.put((module, task))
    self.queues.append((queue, priority, module))
    self.queues.sort(key=lambda q: -q[1])
    self.start_thread_filler()

  def start_thread_filler(self):
    if self.closing or self.thread_filler != None or len(self.queues) == 0: return
    self.logger.info('Starting up module thread filler...')
    self.thread_filler = Thread(target=self.fill_threads, name='Module-Thread-Filler')
    self.thread_filler.start()

  def fill_threads(self):
    while len(self.queues) > 0 and not self.closing:
      queue, queue_index = self.get_queue()
      if queue is None:
        time.sleep(0.5)
        continue
      
      if queue.empty():
        self.queues.pop(queue_index)
        continue

      index = self.new_thread_slot()
      if index is None:
        time.sleep(0.5)
        continue

      module, task = queue.get()
      if self.is_task_invalid(module, task):
        continue

      self.start_thread(module, task, index)
      self.modules_in_use.append(module)
    
    self.logger.info(f"{'' if self.closing else 'Module queue is empty. '}Stopping module thread filler...")
    self.thread_filler = None
  
  def get_queue(self):
    for i, (queue, _, module) in enumerate(self.queues):
      if module not in self.modules_in_use:
        return queue, i
    return None, None

  def start_thread(self, module, task, index):
    task_switcher = {
      ThreadTask.INIT: 'Initialising',
      ThreadTask.RUN: 'Running'
    }

    def wrapper():
      self.logger.info(f'{task_switcher[task]} module: `{module.name}`')
      self.get_func_from_task(module, task)()
      self.threads[index] = None
      self.modules_in_use.remove(module)

    name = self.get_thread_name(module, task)
    self.logger.info(f'Starting thread: {name}')
    self.threads[index] = Thread(target=wrapper, name=name)
    self.threads[index].start()
  
  @staticmethod
  def is_task_invalid(module, task):
    return module.module is not None and task == ThreadTask.INIT
  
  @staticmethod
  def get_func_from_task(module, task):
    task_switcher = {
      ThreadTask.INIT: module.initialise,
      ThreadTask.RUN: module.run
    }
    return task_switcher[task]

  @staticmethod
  def get_thread_name(module, task):
    task_switcher = {
      ThreadTask.INIT: 'init',
      ThreadTask.RUN: 'run'
    }
    return f'Module-Thread ({module.name})[{task_switcher[task]}]'
