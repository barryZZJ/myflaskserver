import requests
from flask import Blueprint, Response, request, make_response
from loguru import logger

# Create a Blueprint object for the main section
bp_redirect = Blueprint('redirect', __name__, url_prefix='/redirect')


@bp_redirect.route('/<path:url>', methods=['GET', 'POST'])
def proxy_url(url):
    logger.info('fetching {}', url)
    try:
        headers = dict(request.headers)
        headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
        headers.pop('Host')
        logger.debug('request headers: {}', headers)
        response = requests.request(request.method, url, headers=headers, params=request.args, data=request.data)

        # logger.debug(response.text)
        logger.debug(f'{response.headers=}')
        content_type = response.headers.get('content-type', 'text/html')
        flask_response = make_response(Response(response.content, status=response.status_code, content_type=content_type))
        for key, value in response.headers.items():
            # TODO may need to remove domain part of cookie
            flask_response.headers[key] = value

        return flask_response

    except requests.RequestException as e:
        return f"Error: {e}", 500

