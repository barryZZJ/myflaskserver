import json
from pathlib import Path

from wecom_responder.utils import WecomReceiver


def load_conf(dir: Path) -> dict:
    conf = dir.joinpath('config.json')
    with conf.open('r', encoding='utf8') as f:
        return json.load(f)


def curr_dir(file: str) -> Path:
    return Path(file).parent

