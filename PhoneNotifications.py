import requests, os
from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
USER_KEY = os.getenv("PUSHOVER_USER_KEY")

class Notifier:
  API_URL = 'https://api.pushover.net/1/messages.json'

  @staticmethod
  def send(title, message, url=None):
    data = {
      'token': API_TOKEN,
      'user': USER_KEY,
      'title': title,
      'message': message
    }
    if url is not None:
      data['url'] = url
    res = requests.post(Notifier.API_URL, data=data)
    return res.ok

if __name__ == "__main__":
  Notifier.send('Test', 'Here is the message')