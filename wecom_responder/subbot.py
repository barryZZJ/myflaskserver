import requests

from wecom_responder.utils.tv_subscribe_bot.tvsubscribebot import TVSubscribeBot
from tvsubscribebot.dumb_bot.dumbbot import Chat, User
from wecom_responder.utils.consts import PERSISTENCE_PKL, DB_SUBBOT, APP_HOST, APP_PORT, DUMBBOT_HOST, DUMBBOT_PORT

subbot = TVSubscribeBot(persistence_filepath=PERSISTENCE_PKL, dbfile_cache=DB_SUBBOT)

def main(listen, port):
    print('starting subbot')
    subbot.listen_forever(listen, port)

@subbot.register_callback
async def send_handled_result_to_flask(result: str, chat: Chat, user: User):
    if not result:
        return
    touid = user.username
    url = f'http://{APP_HOST}:{APP_PORT}//subscribe_chan_send/{touid}'
    params = {'result': result}
    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        print(f"Redirect subbot result successful: {response.text}")
    except requests.RequestException as e:
        print(f"Redirect subbot result failed: {e}")

if __name__ == '__main__':
    main(DUMBBOT_HOST, DUMBBOT_PORT)
