from flask import Blueprint

# Create a Blueprint object for the main section
bp_root = Blueprint('root', __name__)

@bp_root.route('/test')
def welcome():
    return 'Welcome to wecom_responder!'

@bp_root.route('/tencent17020964508655017006.txt')
def wxverify():
    return '5211949090338753366'
