from pathlib import Path

from loguru import logger

logfile = Path(__file__).parents[1].joinpath('responder.log')

logger.add(str(logfile), rotation='1 day', retention='3 days')
