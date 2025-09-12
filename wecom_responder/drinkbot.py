import requests

from wecom_responder.utils._dailydrinknotifybot import DailyDrinkNotifyBot
from tvsubscribebot.dumb_bot.dumbbot import Chat, User
from wecom_responder.utils.config import config_manager
from wecom_responder.utils.consts import PERSISTENCE_PKL_BY_NAME

drinkbot = DailyDrinkNotifyBot(persistence_filepath=PERSISTENCE_PKL_BY_NAME('drinkbot'))

def main(listen, port):
    print('starting subbot')
    drinkbot.listen_forever(listen, port)

@drinkbot.register_callback
async def send_handled_result_to_flask(result: str, chat: Chat, user: User):
    if not result:
        return
    touid = user.username
    APP_HOST = config_manager['APP_HOST']
    APP_PORT = config_manager['APP_PORT']
    if result.startswith('b64:'):
        result = result[4:]
        url = f'http://{APP_HOST}:{APP_PORT}/drink_chan_send/image/{touid}'
    else:
        url = f'http://{APP_HOST}:{APP_PORT}/drink_chan_send/{touid}'
    params = {'result': result}
    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        print(f"Redirect subbot result successful: {response.text}")
    except requests.RequestException as e:
        print(f"Redirect subbot result failed: {e}")

if __name__ == '__main__':
    DUMBBOT_HOST = config_manager['DUMBBOT_HOST']
    DRINKBOT_PORT = config_manager['DRINKBOT_PORT']
    main(DUMBBOT_HOST, DRINKBOT_PORT)
