import requests
from flask import Blueprint, Response, stream_with_context, render_template
from loguru import logger
from wecomsan import WecomSan

from wecom_responder.utils.config import load_conf, curr_dir

# Create a Blueprint object for the main section
bp = Blueprint('wecom_temp_media', __name__, url_prefix='/wecom_temp_media')


@bp.route('/file/<media_id>')
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


@bp.route('/<media_id>')
def temp_media_redirect(media_id):
    conf = load_conf(curr_dir(__file__))
    wecombot = WecomSan(**conf['bot'])
    redirect_url = f'https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token={wecombot.access_token}&media_id={media_id}'
    logger.info('media_id: {}', media_id)
    logger.info('target url: {}', redirect_url)
    resp = requests.get(redirect_url, stream=True)
    # html_content = resp.content.decode('utf8')
    # logger.debug(html_content)
    mimetype = 'text/html; charset=utf-8'
    return Response(resp.content, mimetype=mimetype)
