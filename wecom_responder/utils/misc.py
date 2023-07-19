import hashlib


def md5int(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)
