import pydantic
import requests
from flask import Blueprint, Response, request, make_response
from loguru import logger

import wecomsan
from wecom_responder.utils.config import load_conf, curr_dir

# Create a Blueprint object for the main section
bp_webhook = Blueprint('webhook', __name__, url_prefix='/webhook')


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

    conf = load_conf(curr_dir(__file__))
    # send textcard instead of text. upload temp file.
    bot = wecomsan.WecomSan(**conf['bot'])
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
