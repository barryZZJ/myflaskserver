from pathlib import Path

ROOT = Path(__file__).parents[1]

ROUTES = ROOT / 'routes'

CACHE_RESPONDER = ROOT / 'data' / 'cache_responder.db'

CACHE_SUBBOT = ROOT / 'data' / 'cache_subbot.db'

LOG = ROOT / 'logs' / 'responder.log'

PERSISTENCE = ROOT / 'data' / 'bot_pkl'

MAX_RESPONSE_BYTES = 2048
