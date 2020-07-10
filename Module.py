from threading import Thread

import LogManager
from PhoneNotifications import Notifier

class ModuleStatus:
  RUNNING = 'Running...'
  PAUSED = 'Paused'

class Module:
  def __init__(self, control, base_class):
    self.control = control
    self.module = base_class(
      logger=LogManager.create_logger(base_class.NAME),
      notifications=Notifier
    )
    self.name = self.module.NAME

    self.status = ModuleStatus.RUNNING
    self.thread = None
  
  def should_occur(self, minutes_past):
    return minutes_past % self.module.OCCUR_EVERY == 0 and self.status == ModuleStatus.RUNNING

  def __call__(self):
    self.thread = Thread(target=self.run, name=f'Module-Thread ({self.module.NAME})')
    self.thread.start()
  
  def run(self):
    self.control.logger.info(f'Running module: {self.module.NAME}')
    try:
      self.module.run()
    except:
      self.control.logger.error(f'There was an error running module: {self.module.NAME}', exc_info=True)
    
    self.thread = None

  @staticmethod
  def is_valid(module):
    return hasattr(module, 'OCCUR_EVERY') and \
      hasattr(module, 'run') and hasattr(module, 'NAME')