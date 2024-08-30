from flask import Blueprint

# Create a Blueprint object for the main section
bp = Blueprint('root', __name__)

@bp.route('/test')
def welcome():
    return 'Welcome to wecom_responder!'

@bp.route('/tencent17020964508655017006.txt')
def wxverify():
    return '5211949090338753366'
