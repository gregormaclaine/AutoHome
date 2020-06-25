from PhoneNotifications import Notifier

class ModuleStatus:
  RUNNING = 'Running...'
  PAUSED = 'Paused'

class Module:
  def __init__(self, base_class, logger):
    self.base_class = base_class

    self.module = base_class(
      logger=logger,
      notifications=Notifier
    )

    self.status = ModuleStatus.RUNNING
  
  def __call__(self):
    self.module.run()

  @staticmethod
  def is_valid(module):
    return hasattr(module, 'OCCUR_EVERY') and \
      hasattr(module, 'run') and hasattr(module, 'NAME')