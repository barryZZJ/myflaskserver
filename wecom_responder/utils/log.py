from pathlib import Path
from loguru import logger
from wecom_responder.utils.consts import LOG

logger.add(str(LOG), rotation='1 day', retention='3 days')
