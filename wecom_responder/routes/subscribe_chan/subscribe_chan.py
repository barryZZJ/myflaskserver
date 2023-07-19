import asyncio
import atexit
import multiprocessing
from typing import Union, Literal
from wecomsan import WecomSan

from wecom_responder.utils import WecomReceiver, TextMessage, BaseMessage, TVSubscribeBot, TextSubmitter, Chat, User
from wecom_responder.utils.consts import MAX_RESPONSE_BYTES, PERSISTENCE_PKL, DB_SUBBOT
from wecom_responder.utils.log import logger
from wecom_responder.utils.config import load_conf, curr_dir
from wecom_responder.utils.manager import ChatManager, UserManager


TO_UID = Union[str, Literal['@all']]
CHATID = int

conf = load_conf(curr_dir(__file__))

# Create a Blueprint object for the main section
bp = WecomReceiver(
    conf['token'],
    conf['encodingAESKey'],
    conf['bot']['cid'],
    'subcribe_chan',
    __name__,
    logger=logger,
    url_prefix='/subscribe_chan',
)
listen = '127.0.0.1'
port = 18888
subbot = TVSubscribeBot(persistence_filepath=PERSISTENCE_PKL, dbfile_cache=DB_SUBBOT)
submitter = TextSubmitter(port=port)
wecombot = WecomSan(**conf['bot'])

manager = multiprocessing.Manager()
touids: dict[Chat, str] = manager.dict()

@bp.receive
def on_text(message: BaseMessage):
    logger.info('new message received: ' + str(message))
    user = UserManager.new_user(message.fromUserName)
    chat = ChatManager.new_chat(user, message.agentID, 'subscribe_chan')
    if isinstance(message, TextMessage):
        logger.info(message)
        touids[chat] = message.fromUserName
        print('receiver touids:', touids)
        if not submitter.submit_text(
            text=message.content,
            date=message.createTime,
            chat=chat,
            from_user=user,
            message_id=message.msgId
        ):
            wecombot.send('后端发送Update失败！', message.fromUserName)


@subbot.register_callback
async def send_handled_result(result: str, chat: Chat, user: User):
    if not result:
        return
    print('sender touids:', touids)
    touid = touids.get(chat, '@all')
    logger.info('Respond with:\n' + result + '\nsend to: ' + touid)
    wecombot.send_autosplit(result, max_content_bytes=MAX_RESPONSE_BYTES)


def listen_forever(listen: str, port: int):
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    subbot.listen_forever(listen, port)


try:
    subbotproc = multiprocessing.Process(target=listen_forever, args=(listen, port), name='subbotproc')
except Exception as e:
    print(f"Error creating subbot process: {e}")

def terminate_subbot():
    print('proc pid:', subbotproc.pid)
    try:
        subbotproc.terminate()
        print('subbot terminated!')
    except Exception as e:
        print('Terminate failed!', str(e))


atexit.register(terminate_subbot)


def run_subbotproc():
    subbotproc.start()

# 报 An attempt has been made to start a new process before the
#         current process has finished its bootstrapping phase.
# 好像是Windows的问题，在Linux上就可以跑了，建议在linux上测试。