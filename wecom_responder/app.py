from flask import Flask
from wecom_responder.routes import bp_verify, bp_subscribe_chan
from wecom_responder.routes.subscribe_chan.subscribe_chan import SubscribeChan

app = Flask(__name__)

if __name__ == '__main__':
    # run sub processes
    subscribe_chan = SubscribeChan()
    subscribe_chan.run_subbotproc()

    app.register_blueprint(bp_verify)
    app.register_blueprint(bp_subscribe_chan)
    # ? 不能是127.0.0.1，否则服务器的端口不开放
    app.run('0.0.0.0', port=23222)
