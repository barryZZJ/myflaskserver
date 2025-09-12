from pathlib import Path

import pydantic
import requests
from flask import Blueprint, Response, request, make_response
from loguru import logger

import wecomsan
from wecom_responder.utils.config import config_manager

# Create a Blueprint object for the main section
bp_webhook = Blueprint('webhook', __name__, url_prefix='/webhook')

current_file = Path(__file__).stem
conf = config_manager.get_param(current_file)

def redirect_rssitem_textcard(data, use_orig_link: bool = True) -> bool:
    # {
    #     "title": "__TITLE__",
    #     "feed": "__FEED__",
    #     "url": "__URL__",
    #     "created": "__DATE_TIMESTAMP__",
    #     "content": "__CONTENT__",
    #     "thumbnail_url": "__THUMBNAIL_URL__"
    # }
    # redirect to wecomchan
    # if 'テレビ王国' in feed.title:
    #     msg = f'来自{feed.title}的更新：\n标题：{rssitem.title}\n内容：\n{rssitem.rich_content}\n查看详情：{rssitem.url}'
    # else:
    #     msg = f'来自{feed.title}的更新：\n标题：{rssitem.title}\n<a href="{rssitem.url}">查看详情</a>'
    # soup = BeautifulSoup(rssitem.rich_content, 'html.parser')
    textcard_title = data['feed']
    textcard_desc = 'Webhook:' + data['title']

    # send textcard instead of text. upload temp file.
    bot = wecomsan.WecomSan(**conf['bots']['mone_chan'])
    try:
        if use_orig_link:
            redirected_url = str(data['url'])
        else:
            raise NotImplementedError
            # redirected_url_base = conf['flask']['wecom_temp_media_route_url']
            # html_content = FreshRssCrawler.render_template(self._template_path, rssitem, feed)
            # resp = bot.upload_html(str(rssitem.item_id), html_content)
            # logger.debug('uploaded html, media_id: {}', resp.media_id)
            # # request flask app for temp_media, and flask (with auth) will redirect to actual url
            # redirected_url = redirected_url_base + '/' + resp.media_id

        resp = bot.send_textcard(textcard_title, textcard_desc, redirected_url)
        return resp.errcode == wecomsan.SUCCESS
    except pydantic.ValidationError as e:
        bot.send_autosplit('error: {}', str(e))
    except requests.RequestException:
        logger.error('RequestException on redirecting rssitem {}', data['title'])
    return False


# def redirect_rssitem_text(data) -> bool:
#     # redirect to wecomchan
#     if 'テレビ王国' in feed.title:
#         msg = f'来自{feed.title}的更新：\n标题：{rssitem.title}\n内容：\n{rssitem.rich_content}\n查看详情：{rssitem.url}'
#     else:
#         msg = f'来自{feed.title}的更新：\n标题：{rssitem.title}\n<a href="{rssitem.url}">查看详情</a>'
#
#     conf = load_conf(CONF)
#     bot = wecomsan.WecomSan(**conf['bot'])
#     try:
#         logger.info('redirecting msg to wecom')
#         return bot.send_autosplit(msg)
#     except pydantic.ValidationError as e:
#         logger.error('pydantic ValidationError')
#         logger.error(traceback.format_exc())
#         return bot.send_autosplit('error: {}', str(e))
#     except requests.RequestException:
#         logger.error('RequestException')
#         logger.error(traceback.format_exc())
#         return False


@bp_webhook.route('/freshrss', methods=['GET', 'POST'])
def freshrss():
    data = request.json
    # print(data)
    # if 'テレビ王国' in data['title']:
    #     redirect_rssitem_text(data)
    # else:
    redirect_rssitem_textcard(data)
    return 'OK', 200


def send_msg(msg: dict) -> Response:
    bot = wecomsan.WecomSan(**conf['bots']['notify_chan'])
    try:
        text, touid = msg['text'], msg.get('touid', '@all')
        resps = bot.send_autosplit2(text, touid=touid)
        for resp in resps:
            if resp.errcode != wecomsan.SUCCESS:
                logger.error(f'Error sending message: {resp.errmsg}')
                return make_response(f'Error sending message: {resp.errmsg}', 500)
        return make_response('Message sent successfully', 200)
    except requests.RequestException as e:
        logger.error(f'RequestException while sending message: {e}')
        return make_response('Failed to send message', 500)

@bp_webhook.route('/msg', methods=['GET', 'POST'])
def msg():
    if request.method == 'GET':
        return make_response('Hi', 200)
    data = request.json
    return send_msg(data)


