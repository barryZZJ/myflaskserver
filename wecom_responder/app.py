import argparse
import os.path

from flask import Flask
from loguru import logger

from wecom_responder.utils.config import config_manager
from wecom_responder.utils.consts import STATIC_FOLDER
from wecom_responder.utils.bp_loader import bp_loader

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/')


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _build_ssl_context(enable_https):
    if not enable_https:
        return None

    cert_file = config_manager['SSL_CERT_FILE']
    key_file = config_manager['SSL_KEY_FILE']
    if cert_file and key_file:
        assert os.path.exists(cert_file) and os.path.exists(key_file), 'SSL_CERT_FILE or SSL_KEY_FILE does not exist.'
        return cert_file, key_file
    if cert_file or key_file:
        raise ValueError('SSL_CERT_FILE and SSL_KEY_FILE must be configured together.')

    logger.warning('HTTPS enabled without SSL_CERT_FILE/SSL_KEY_FILE; using adhoc self-signed certificate.')
    return 'adhoc'


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--ipv6', action='store_true')
    parser.add_argument('--https', action='store_true')
    return parser.parse_args()

def register_all_bps():
    """注册所有已加载的bp"""
    loaded_bps = bp_loader.load_all_enabled_bps()

    for module_name, bps in loaded_bps.items():
        for bp in bps:
            try:
                app.register_blueprint(bp)
                logger.info(f"已注册bp: {module_name}.{bp.name}")
            except Exception as e:
                logger.error(f"注册bp {module_name}.{bp.name} 失败: {e}")

# 注册所有bp
register_all_bps()

if __name__ == '__main__':
    print('Starting wecom_responder...')
    args = _parse_args()
    APP_HOST = config_manager['APP_HOST']
    APP_PORT = config_manager['APP_PORT']
    APP_HOST6 = config_manager['APP_HOST6']
    HTTPS_ENABLED = _as_bool(config_manager['HTTPS_ENABLED']) or args.https
    ssl_context = _build_ssl_context(HTTPS_ENABLED)
    host = APP_HOST6 if args.ipv6 else APP_HOST
    scheme = 'https' if ssl_context else 'http'

    logger.info(f'Starting {scheme} server on {host}:{APP_PORT}')
    app.run(
        host=host,
        port=APP_PORT,
        debug=args.debug,
        use_reloader=args.debug,
        ssl_context=ssl_context,
    )
