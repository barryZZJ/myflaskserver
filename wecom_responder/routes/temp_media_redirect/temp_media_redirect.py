import re

import requests
from flask import Blueprint, Response, stream_with_context, render_template, request
from loguru import logger
from wecomsan import WecomSan

from wecom_responder.utils.config import load_conf, curr_dir

# Create a Blueprint object for the main section
bp_temp_media_redirect = Blueprint('wecom_temp_media', __name__, url_prefix='/wecom_temp_media')


def modify_html(text: str, is_ua_wechat: bool) -> str:
    pat = re.compile(r'<a id="redirect" href="([^"]+?)" class="wx_tap_link js_wx_tap_highlight weui-wa-hotarea">')
    match = pat.search(text)
    if match:
        refuse_redirect = ('tvkingdom' in pat.search(text).group(1)) and is_ua_wechat
        if refuse_redirect:
            return pat.sub('<a href="javascript:void(0);" class="wx_tap_link js_wx_tap_highlight weui-wa-hotarea" onclick="alert(\'请在浏览器中打开！\');">', text, count=1)
    return text


@bp_temp_media_redirect.route('/file/<media_id>')
def temp_media_download(media_id):
    conf = load_conf(curr_dir(__file__))
    wecombot = WecomSan(**conf['bot'])
    redirect_url = f'https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token={wecombot.access_token}&media_id={media_id}'
    logger.info('media_id: {}', media_id)
    logger.info('target url: {}', redirect_url)
    resp = requests.get(redirect_url, stream=True)

    headers = resp.headers
    return_headers = {
        key: value
        for key, value in headers.items()
        if key.lower() not in ("content-length", "connection", "content-encoding")
    }

    return Response(
        stream_with_context(resp.iter_content(chunk_size=8192)),
        headers=return_headers
    )


@bp_temp_media_redirect.route('/<media_id>')
def temp_media_redirect(media_id):
    conf = load_conf(curr_dir(__file__))
    wecombot = WecomSan(**conf['bot'])
    redirect_url = f'https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token={wecombot.access_token}&media_id={media_id}'
    logger.info('media_id: {}', media_id)
    logger.info('target url: {}', redirect_url)
    resp = requests.get(redirect_url, stream=True)
    user_agent = request.headers.get('User-Agent')
    is_wechat_ua = 'MicroMessenger' in user_agent
    # html_content = resp.content.decode('utf8')
    # logger.debug(html_content)
    mimetype = 'text/html; charset=utf-8'
    modified_html = modify_html(resp.content.decode('utf8'), is_wechat_ua).encode('utf8')
    return Response(modified_html, mimetype=mimetype)
