import requests
from flask import Blueprint, Response, request, make_response
from loguru import logger

# Create a Blueprint object for the main section
bp_redirectlocal = Blueprint('redirectlocal', __name__)

ports = {
    'wireguard': 11800,  # same as mydjangoserver/start
}

# redirect django requests to django server ====================================
@bp_redirectlocal.route('/static/admin/<path:url>', methods=['GET'])
def proxy_django_static(url):
    logger.info('fetching static/admin/{}', url)
    return proxy_url(ports['django'], f'static/admin/{url}')

@bp_redirectlocal.route('/admin/<path:url>', methods=['GET'])
def proxy_django_admin(url):
    logger.info('fetching admin/{}', url)
    return proxy_url(ports['django'], f'admin/{url}')
# ==============================================================================

@bp_redirectlocal.route('/redirectlocal/<key>/', defaults={'url': ''}, methods=['GET', 'POST'])
@bp_redirectlocal.route('/redirectlocal/<key>/<path:url>', methods=['GET', 'POST'])
def proxy_url_by_name(key: str, url):
    return proxy_url(ports[key], url)

@bp_redirectlocal.route('/redirectlocal/<int:port>/', defaults={'url': ''}, methods=['GET', 'POST'])
@bp_redirectlocal.route('/redirectlocal/<int:port>/<path:url>', methods=['GET', 'POST'])
def proxy_url(port: int, url):
    url = f'http://127.0.0.1:{port}/{url}'
    try:
        logger.info('fetching {}', url)
        headers = dict(request.headers)
        headers.pop('Host')
        logger.debug('request headers: {}', headers)
        response = requests.request(request.method, url, headers=headers, params=request.args, data=request.form, allow_redirects=True, cookies=request.cookies)

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
