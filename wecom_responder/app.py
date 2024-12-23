import sys

from flask import Flask

from wecom_responder.utils.consts import APP_PORT, APP_HOST

# import logging
#
#
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.DEBUG
# )

app = Flask(__name__)

from wecom_responder.routes import bp_verify, bp_subscribe_chan_recv, bp_subscribe_chan_send, bp_temp_media_redirect, \
bp_redirect, bp_redirectlocal, bp_root, bp_webhook
# from wecom_responder.routes import bp_wireguard, bp_wireguard_chan

app.register_blueprint(bp_verify)
app.register_blueprint(bp_subscribe_chan_recv)
app.register_blueprint(bp_subscribe_chan_send)
app.register_blueprint(bp_temp_media_redirect)
app.register_blueprint(bp_redirect)
app.register_blueprint(bp_redirectlocal)
app.register_blueprint(bp_root)
# app.register_blueprint(bp_wireguard)
# app.register_blueprint(bp_wireguard_chan)
app.register_blueprint(bp_webhook)

if __name__ == '__main__':
    # ? 不能是127.0.0.1，否则服务器的端口不开放
    print('Starting wecom_responder...')
    if sys.argv[-1] == '--debug':
        app.run(APP_HOST, port=APP_PORT, debug=True)
    else:
        app.run(APP_HOST, port=APP_PORT)
