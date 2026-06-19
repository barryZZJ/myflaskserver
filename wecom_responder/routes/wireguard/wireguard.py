from flask import Blueprint, url_for

# Create a Blueprint object for the main section
bp_wireguard = Blueprint('wireguard', __name__, url_prefix='/wireguard')

@bp_wireguard.route('/')
def wireguard():
    return url_for('redirectlocal.proxy_url_by_name', key='wireguard')
