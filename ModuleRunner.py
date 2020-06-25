from threading import Thread, current_thread

def complete_queue_tasks(queue, logger, workers, num):
  try:
    while True:
      module = queue.get()
      if module is None:
        logger.info(f'Thread-{num} closing...')
        break
      logger.info(f'Running module: {module.base_class.NAME}')
      try:
        module()
      except:
        logger.error(f'There was an error running module: {module.base_class.NAME}', exc_info=True)
  except Exception:
    logger.critical(f'An error occured in Thread-{num}', exc_info=True)
    workers.remove(current_thread())
    logger.info(f'Thread-{num} closing...')

class ModuleRunner:
  NUM_TASK_THREADS = 3

  def __init__(self, parent):
    self.master_logger = parent.logger
    self.queue = parent.queue

    self.workers = []
    self.current_worker_num = 1

    self.master_logger.info(f"Initialising {ModuleRunner.NUM_TASK_THREADS} worker thread{'' if ModuleRunner.NUM_TASK_THREADS == 1 else 's'}...")
    self.fill_workers()
  
  def fill_workers(self):
    lacking_workers = ModuleRunner.NUM_TASK_THREADS - len(self.workers)
    if lacking_workers > 0:
      for _ in range(lacking_workers):
        self.add_new_worker()
  
  def add_new_worker(self):
    thread_args = (self.queue, self.master_logger, self.workers, self.current_worker_num)
    worker = Thread(target=complete_queue_tasks, args=thread_args, name=f'Thread-{self.current_worker_num}')
    worker.start()
    self.workers.append(worker)
    self.master_logger.info(f'Added new worker thread (Thread-{self.current_worker_num}); Total threads now: {len(self.workers)}/{ModuleRunner.NUM_TASK_THREADS}')
    self.current_worker_num += 1

  def stop_workers(self):
    for _ in self.workers:
      self.queue.put(None)
