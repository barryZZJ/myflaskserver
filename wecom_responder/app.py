from multiprocessing import freeze_support

from flask import Flask

# import logging
#
#
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.DEBUG
# )

app = Flask(__name__)

if __name__ == '__main__':
    # run sub processes
    freeze_support()
    from wecom_responder.routes import bp_verify, bp_subscribe_chan, bp_temp_media_redirect
    from wecom_responder.routes.subscribe_chan.subscribe_chan import run_subbotproc
    run_subbotproc()

    app.register_blueprint(bp_verify)
    app.register_blueprint(bp_subscribe_chan)
    app.register_blueprint(bp_temp_media_redirect)
    # ? 不能是127.0.0.1，否则服务器的端口不开放
    app.run('0.0.0.0', port=23222)
