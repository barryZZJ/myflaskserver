import sys
from flask import Flask
from loguru import logger

from wecom_responder.utils.consts import STATIC_FOLDER, APP_PORT, APP_HOST, APP_HOST6
from wecom_responder.utils.bp_loader import bp_loader

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/')

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
    if sys.argv[-1] == '--debug':
        app.run(APP_HOST, port=APP_PORT, debug=True)
    elif sys.argv[-1] == '--ipv6':
        app.run(host=APP_HOST6, port=APP_PORT, debug=False, use_reloader=False)
    else:
        app.run(host=APP_HOST, port=APP_PORT, debug=False, use_reloader=False)