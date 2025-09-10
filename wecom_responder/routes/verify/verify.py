from flask import Blueprint

# Create a Blueprint object for the main section
bp_verify = Blueprint('verify', __name__, url_prefix='/')
# note: moved to static/xx.txt

@bp_verify.route('/WW_verify_Ua7WxLfBndo8F2SR.txt')
def verify():
    return 'Ua7WxLfBndo8F2SR'

@bp_verify.route('/WW_verify_qNHZNNTXbAbd5hPr.txt')
def verify2():
    return 'qNHZNNTXbAbd5hPr'

@bp_verify.route('/tencent17020964508655017006.txt')
def wxverify():
    return '5211949090338753366'
