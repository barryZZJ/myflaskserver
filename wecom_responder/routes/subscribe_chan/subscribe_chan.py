from typing import Union, Literal

from flask import Blueprint, request

from wecomsan import WecomSan

from wecom_responder.utils import WecomReceiver, TextMessage, BaseMessage, TextSubmitter
from wecom_responder.utils.consts import MAX_RESPONSE_BYTES, DUMBBOT_PORT, DUMBBOT_HOST
from wecom_responder.utils.log import logger
from wecom_responder.utils.config import load_conf, curr_dir
from wecom_responder.utils.manager import ChatManager, UserManager


TO_UID = Union[str, Literal['@all']]
CHATID = int

conf = load_conf(curr_dir(__file__))

# Create a Blueprint object for the main section
# receive messages from wecom user
bp_recv = WecomReceiver(
    conf['token'],
    conf['encodingAESKey'],
    conf['bot']['cid'],
    'subcribe_chan',
    __name__,
    logger=logger,
    url_prefix='/subscribe_chan',
)

submitter = TextSubmitter(listen=DUMBBOT_HOST, port=DUMBBOT_PORT)
wecombot = WecomSan(**conf['bot'])

# touids: dict[Chat, str] = manager.dict()

# send messages to wecom user received from subbot
bp_send = Blueprint('subscribe_chan_send', __name__, url_prefix='/subscribe_chan_send')

@bp_recv.receive
def on_text(message: BaseMessage):
    logger.info('new message received: ' + str(message))
    user = UserManager.new_user(message.fromUserName)
    chat = ChatManager.new_chat(user, message.agentID)
    if isinstance(message, TextMessage):
        # touids[chat] = message.fromUserName
        # print('receiver touids:', touids)
        if not submitter.submit_text(
            text=message.content,
            date=message.createTime,
            chat=chat,
            from_user=user,
            message_id=message.msgId
        ):
            wecombot.send('后端发送Update失败！', message.fromUserName)


@bp_send.route('/<touid>', methods=['POST'])
def send_handled_result_to_user(touid: str):
    result = request.json.get('result', '')
    if not result:
        return
    # print('sender uid:', touid)
    # touid = touids.get(chat, '@all')
    logger.info('Send respond to {} with:\n{}', touid, result)
    succ = wecombot.send_autosplit(result, touid, max_content_bytes=MAX_RESPONSE_BYTES)
    if not succ:
        logger.error('send_autosplit returned False!')
    return 'OK'