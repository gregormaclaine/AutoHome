import logging

def init():
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)-15s | %(levelname)-8s]: %(message)s',
    datefmt='%d-%m-%y %H:%M:%S',
    filename='logs/current.log'
  )

def applyPadding(name, num=15):
  extra = num - len(name)
  return f"{' ' * (extra // 2 + extra % 2)}{name}{' ' * (extra // 2)}"

def create_logger(name):
  logger = logging.getLogger(applyPadding(name.upper()))
  logger.addHandler(logging.StreamHandler())
  return logger