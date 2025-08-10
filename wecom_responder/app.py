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

app = Flask(__name__, static_folder='static', static_url_path='/')

from wecom_responder.routes import bp_verify, bp_recv_from_subscribe_chan, bp_send_to_subscribe_chan, bp_temp_media_redirect, \
bp_redirect, bp_redirectlocal, bp_root, bp_webhook, bp_send_to_drink_chan, bp_recv_from_drink_chan, bp_ddredirect
# from wecom_responder.routes import bp_wireguard, bp_wireguard_chan

app.register_blueprint(bp_verify)
app.register_blueprint(bp_recv_from_subscribe_chan)
app.register_blueprint(bp_send_to_subscribe_chan)
app.register_blueprint(bp_recv_from_drink_chan)
app.register_blueprint(bp_send_to_drink_chan)
app.register_blueprint(bp_temp_media_redirect)
app.register_blueprint(bp_redirect)
app.register_blueprint(bp_redirectlocal)
app.register_blueprint(bp_root)
# app.register_blueprint(bp_wireguard)
# app.register_blueprint(bp_wireguard_chan)
app.register_blueprint(bp_webhook)
app.register_blueprint(bp_ddredirect)

if __name__ == '__main__':
    # ? 不能是127.0.0.1，否则服务器的端口不开放
    print('Starting wecom_responder...')
    if sys.argv[-1] == '--debug':
        app.run(APP_HOST, port=APP_PORT, debug=True)
    else:
        app.run(APP_HOST, port=APP_PORT)
