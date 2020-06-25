import socket
from threading import Thread

from TelnetServerOutputController import TelnetServerOutputController

class TelnetServer:
  PORT = 23
  COMMAND_PREFIX = 'AutoHome >'

  def __init__(self, parent):
    self.parent = parent

    self.out = TelnetServerOutputController(self)

    self.logger = parent.__class__.create_logger('TELNETSERVER')

    self.conn = None
    self.closing = None  # None | 'server' | 'connection'

    self.logger.info('Initialising TelnetServer...')
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.bind(('', TelnetServer.PORT))

    self.thread = Thread(target=self.listen, name='TelnetServer')
    self.thread.start()
  
  def send(self, s):
    if self.conn is not None:
      self.conn.send(s.encode())
  
  def receive(self):
    # Is there a connection
    if self.conn is None:
      return None

    # Can I get any data
    try:
      data = self.conn.recv(1024)
    except BrokenPipeError:
      self.closing = 'server'
      return None
    if not data:
      self.closing = 'connection'
      return None

    # Can I understand the data
    try:
      decoded = data.decode('utf-8')
    except UnicodeDecodeError:
      self.logger.warning('Unknown Input: ' + str(data))
      return None
    
    # Return the data
    filtered = ''.join([c for c in decoded if c.isalnum() or c in '\b\n '])
    return filtered
  
  def receive_full(self):
    current = ''
    while True:
      data = self.receive()
      if data is None:
        if self.closing is not None:
          return None
        else:
          continue
      elif data == '\n':
        return current
      elif data == '\b':
        current = current[:-1]
        self.send(' \b')
      else:
        current += data
  
  def prompt(self, question):
    if (self.conn is None) or (self.closing is not None):
      return None
    
    self.send(question)
    data = self.receive_full()
    self.send('\r\n')
    return data

  def confirm(self):
    return self.prompt('Are you sure you want to do this? (y/n) >') == 'y'
    
  def close(self):
    self.logger.info('Closing TelnetServer...')
    if self.conn is not None:
      self.conn.shutdown(socket.SHUT_RDWR)
    self.socket.close()

  def on_receive(self, line):
    if line != '':
      self.send('\r\n')
      self.logger.info(f'Received command: `{line}`')
      self.out.handle_command(line)
    self.send(f'\r\n{TelnetServer.COMMAND_PREFIX}')

  def listen(self):
    self.socket.listen(1)
    self.logger.info(f'Server listening on port {TelnetServer.PORT}...')
    while True:
      if self.closing == 'server':
        break
      elif self.closing == 'connection':
        self.closing = None
      self.conn = None
      try:
        self.conn, addr = self.socket.accept()
      except OSError:
        break
      with self.conn:
        self.send(TelnetServer.COMMAND_PREFIX)
        self.logger.info(f'New connection opened with {addr}')
        while True:
          if self.closing is not None:
            break
          data = self.receive_full()
          if data is None: continue

          elif data == 'quit':
            self.logger.info(f'Received command: `quit`\nClosing connection...')
            break
          self.on_receive(data)
      
      self.logger.info(f'Connection with {addr} has closed')
