from threading import Thread
from datetime import datetime, timedelta

import LogManager
from PhoneNotifications import Notifier

def format_timedelta(td):
  s = td.seconds
  if s > 60 * 60 * 24 * 2:
    return 'Multiple days ago'

  if s < 60:            num, msmt = s, 'second'
  elif s < 60 * 60 * 2: num, msmt = s // 60, 'minute'
  else:                 num, msmt = s // (60 * 60), 'hour'
  
  return f"{num} {msmt}{'' if num == 1 else 's'} ago"

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

    self.latest_run = None

    self.status = ModuleStatus.RUNNING
    self.thread = None
  
  @property
  def time_since_last_run(self):
    if self.latest_run is None: return 'Not yet ran'
    return format_timedelta(datetime.now() - self.latest_run)
  
  def should_occur(self, minutes_past):
    return minutes_past % self.module.OCCUR_EVERY == 0 and self.status == ModuleStatus.RUNNING

  def __call__(self):
    self.thread = Thread(target=self.run, name=f'Module-Thread ({self.module.NAME})')
    self.thread.start()
  
  def run(self):
    self.control.logger.info(f'Running module: {self.module.NAME}')
    try:
      self.latest_run = datetime.now()
      self.module.run()
    except:
      self.control.logger.error(f'There was an error running module: {self.module.NAME}', exc_info=True)
    
    self.thread = None

  @staticmethod
  def is_valid(module):
    return hasattr(module, 'OCCUR_EVERY') and \
      hasattr(module, 'run') and hasattr(module, 'NAME')