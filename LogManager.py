import logging, os, re, uuid, base64

def uniqid():
	x = uuid.uuid1()
	return base64.urlsafe_b64encode(x.bytes).decode()

def init(new_file):
  if new_file and os.path.isfile('logs/current.log'):
    with open('logs/current.log', 'r') as f:
      first_date = re.search(r'(\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})|$', f.read()).group()
      identifier = first_date.replace(':', '_') if first_date != '' else uniqid()
    os.rename('logs/current.log', f'logs/archive {identifier}.log')

  with open('logs/current.log', 'a') as f:
    f.write('=' * 100 + '\n')

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
