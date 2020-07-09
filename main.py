import time, sys

from ModuleRunner import ModuleRunner
from TelnetServer import TelnetServer
import LogManager

def has_flags(*flags):
  return any([flag in sys.argv[1:] for flag in flags])

testing_mode = has_flags('--test', '-t')
LogManager.init(has_flags('--new', '-n'))

class Main:
  def __init__(self):
    self.logger = LogManager.create_logger('MASTER')

    self.closing = False

    self.logger.info('Initialising AutoHome server...')
    self.mr = ModuleRunner(self)
    self.server = TelnetServer(self)

    self.mainloop()
      
  def close_server(self):
    self.logger.info('Closing Autohome server...')
    self.server.close()
    self.mr.close()
    self.closing = True
    exit()

  def mainloop(self):
    minutes_past = 0.0
    try:
      while True:
        if self.closing: break

        self.mr.run_modules(minutes_past)

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