import time
from threading import Thread

from flask import Blueprint, url_for, redirect

from wgfrontend import exechelper
from wecomsan import WecomSan

from wecom_responder.utils import WecomReceiver, TextMessage, BaseMessage
from wecom_responder.utils.consts import MAX_RESPONSE_BYTES
from wecom_responder.utils.log import logger
from wecom_responder.utils.config import load_conf, curr_dir

# 使用说明：
# 先在企业微信机器人Wireguard酱里启动wgfrontend服务，然后进行配置。超时10分钟，或手动指定后，自动关闭wgfrontend服务。

# 跳转至wireguard配置页面
bp_wireguard = Blueprint('wireguard', __name__, url_prefix='/wireguard')

@bp_wireguard.route('/')
def wireguard():
    return redirect(url_for('redirectlocal.proxy_url_by_name', key='wireguard'))

conf = load_conf(curr_dir(__file__))

# Create a Blueprint object for the main section
# receive messages from wecom user
bp_wireguard_chan = WecomReceiver(
    conf['token'],
    conf['encodingAESKey'],
    conf['bot']['cid'],
    'wireguard_chan',
    __name__,
    logger=logger,
    url_prefix='/wireguard_chan',
)

wecombot = WecomSan(**conf['bot'])
eh = exechelper.ExecHelper()

USAGES = {
    'help': dict(msg='help - 显示此帮助'),
    'url': dict(msg='url - 显示wireguard配置页面地址'),
    'start': dict(msg='start <timeout=10> - 启动wgfrontend服务, timeout分钟后自动关闭，0表示不自动关闭', action='start', service='wgfrontend'),
    'stop': dict(msg='stop - 停止wgfrontend服务', action='stop', service='wgfrontend'),
    'reload': dict(msg='reload - 重载wireguard服务', action='reload', service='wg-quick@wg_rw'),
}

def systemctl(action, service):
    command = f'systemctl {action} "{service}"'
    out, err, ret = eh.execute(command, suppressoutput=True, suppresserrors=True)
    return out, err, ret

@bp_wireguard_chan.receive
def on_text(message: BaseMessage):
    logger.info('new message received: ' + str(message))
    if isinstance(message, TextMessage):
        # 处理消息
        cmd, *args = message.content.lower().split(' ')
        match = USAGES.get(cmd, USAGES['help'])
        print(match)
        if cmd == 'help':
            usages = [match['msg'] for match in USAGES.values()]
            result = conf['url']
            result += '\n'
            result = '\n'.join(usages)
        elif cmd == 'url':
            result = conf['url']
        else:
            try:
                out, err, ret = systemctl(match['action'], match['service'])
                result = f'执行 {match["action"]} {match["service"]} 成功！'
            except Exception as e:
                result = f'执行 {match["action"]} {match["service"]} 失败：\n{e}'
        if cmd == 'start':
            try:
                timeout = float(args[0]) if args else 10
                thread = Thread(target=lambda: [time.sleep(timeout * 60), systemctl('stop', 'wgfrontend')])
                thread.start()
            except Exception as e:
                result += f'\n定时自动关闭wgfrontend失败：\n{e}'
        logger.info('Send respond to {} with:\n{}', message.fromUserName, result)
        succ = wecombot.send_autosplit(result, message.fromUserName, max_content_bytes=MAX_RESPONSE_BYTES)
        if not succ:
            logger.error('send_autosplit returned False!')
        return 'OK'


