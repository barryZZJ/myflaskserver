import requests
from flask import Blueprint, Response, request
from loguru import logger

# Create a Blueprint object for the main section
bp = Blueprint('redirect', __name__, url_prefix='/redirect')


@bp.route('/<path:url>')
def proxy_url(url):
    logger.info('fetching {}', url)
    try:
        headers = dict(request.headers)
        headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
        headers.pop('Host')
        logger.debug('request headers: {}', headers)
        response = requests.get(url, headers=headers)

        logger.debug(response.text)
        content_type = response.headers.get('content-type', 'text/html')
        return Response(response.content, status=response.status_code, content_type=content_type)

    except requests.RequestException as e:
        return f"Error: {e}", 500

