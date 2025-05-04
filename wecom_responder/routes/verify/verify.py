from flask import Blueprint

# Create a Blueprint object for the main section
bp_verify = Blueprint('verify', __name__, url_prefix='/verify')
# note: moved to files/xx.txt

@bp_verify.route('/WW_verify_Ua7WxLfBndo8F2SR.txt')
def verify():
    return 'Ua7WxLfBndo8F2SR'
