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

PERSISTENCE_PKL_BY_NAME = lambda name: ROOT / 'data' / f'{name}_pkl'

MAX_RESPONSE_BYTES = 2048

DUMBBOT_HOST = '127.0.0.1'
SUBBOT_PORT = 18888
DRINKBOT_PORT = 18889

APP_HOST = '0.0.0.0'
APP_HOST6 = '::'
APP_PORT = 14222