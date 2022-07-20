from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
NCS_HEADERS = {
        'authority': 'ncs.io',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }
INSTA_HEADERS  = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'x-asbd-id': '198387',
    'x-ig-app-id': '936619743392459',
    'x-ig-www-claim': 'hmac.AR2gTt7P1OeXjKb4651zlr-NZb_HIPf1uEAgkcZAiwsFFLbv',
}


NCS_LOGIN = os.environ.get('NCS_LOGIN')
NCS_PASSWORD = os.environ.get('NCS_PASSWORD')

INSTA_LOGIN = os.environ.get('INSTA_LOGIN')
INSTA_PASSWORD = os.environ.get('INSTA_PASSWORD')

TOKEN = os.environ.get('TOKEN')

if not all([NCS_LOGIN, NCS_PASSWORD, INSTA_LOGIN, INSTA_PASSWORD, TOKEN]):
    raise TypeError('Enter login, password and token, not NoneType')