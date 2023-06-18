from wecom_responder.utils import TVSubscribeBot, WecomSan, WecomReceiver, TextMessage, BaseMessage
from wecom_responder.utils.consts import MAX_RESPONSE_SIZE
from wecom_responder.utils.log import logger
from wecom_responder.utils.config import load_conf, curr_dir
from wecom_responder.utils.messagemanager import message_manager
from wecom_responder.utils.misc import split_text

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
subbot = TVSubscribeBot()
wecombot = WecomSan(**conf['bot'])


@bp.receive
def on_msg(msg: BaseMessage):
    # TODO catch error from subbot.handle_msg
    user = message_manager.set_default_user(msg.fromUserName)
    chat = message_manager.set_default_chat(user, msg.agentID, 'subscribe_chan')
    if isinstance(msg, TextMessage):
        logger.info(msg)
        if respMsg := subbot.handle_msg(msg.content, msg.createTime, chat, user):
            logger.info('Respond with:\n' + respMsg)
            for chunk in split_text(respMsg, MAX_RESPONSE_SIZE):
                wecombot.send(chunk)
