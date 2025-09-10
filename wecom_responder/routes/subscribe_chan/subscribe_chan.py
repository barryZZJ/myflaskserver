from pathlib import Path

from flask import Blueprint, request

from wecomsan import WecomSan

from wecom_responder.utils import WecomReceiver, TextMessage, BaseMessage, TextSubmitter
from wecom_responder.utils.consts import MAX_RESPONSE_BYTES, SUBBOT_PORT, DUMBBOT_HOST
from wecom_responder.utils.log import logger
from wecom_responder.utils.config import config_manager
from wecom_responder.utils.manager import ChatManager, UserManager


current_file = Path(__file__).stem
conf = config_manager.get_param(current_file)

# Create a Blueprint object for the main section
# receive messages from wecom user
bp_recv_from_subscribe_chan = WecomReceiver(
    conf['token'],
    conf['encodingAESKey'],
    conf['bot']['cid'],
    'recv_from_subscribe_chan',
    __name__,
    logger=logger,
    url_prefix='/subscribe_chan_recv',
)

submitter = TextSubmitter(listen=DUMBBOT_HOST, port=SUBBOT_PORT)
wecombot = WecomSan(**conf['bot'])

# touids: dict[Chat, str] = manager.dict()

# send messages to wecom user received from subbot
bp_send_to_subscribe_chan = Blueprint('send_to_subscribe_chan', __name__, url_prefix='/subscribe_chan_send')

@bp_recv_from_subscribe_chan.receive
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


@bp_send_to_subscribe_chan.route('/<touid>', methods=['POST'])
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