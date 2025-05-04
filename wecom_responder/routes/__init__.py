from .verify.verify import bp_verify
from .subscribe_chan.subscribe_chan import bp_recv_from_subscribe_chan, bp_send_to_subscribe_chan
from .drink_chan.drink_chan import bp_send_to_drink_chan, bp_recv_from_drink_chan
from .temp_media_redirect.temp_media_redirect import bp_temp_media_redirect
from .redirect.redirect import bp_redirect
from .redirect.redirectlocal import bp_redirectlocal
from .root.root import bp_root
# from .wireguard.wireguard_chan import bp_wireguard_chan, bp_wireguard
from .webhook.webhook import bp_webhook