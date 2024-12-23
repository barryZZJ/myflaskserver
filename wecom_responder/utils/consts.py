from pathlib import Path

ROOT = Path(__file__).parents[1]

ROUTES = ROOT / 'routes'

DB_RESPONDER = ROOT / 'data' / 'cache_responder.db'
DB_RESPONDER.parent.mkdir(exist_ok=True)

DB_SUBBOT = ROOT / 'data' / 'cache_subbot.db'

DB_JOBSTORE = 'mongodb://127.0.0.1:27017/admin?retryWrites=true&w=majority'

LOG = ROOT / 'logs' / 'responder.log'

FILES = ROOT / 'files'
PDFJS = FILES / 'pdf.js'

PERSISTENCE_PKL = ROOT / 'data' / 'bot_pkl'

MAX_RESPONSE_BYTES = 2048

DUMBBOT_HOST = '127.0.0.1'
DUMBBOT_PORT = 18888

APP_HOST = '0.0.0.0'
APP_PORT = 23222