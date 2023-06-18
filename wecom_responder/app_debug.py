from flask import Flask
from wecom_responder.routes import bp_verify, bp_subscribe_chan

app = Flask(__name__)

if __name__ == '__main__':
    app.register_blueprint(bp_verify)
    app.register_blueprint(bp_subscribe_chan)
    app.run('0.0.0.0', port=23222, debug=True)
