import hashlib


def md5int(s: str, digits: int) -> int:
    res = str(int(hashlib.md5(s.encode()).hexdigest(), 16))
    res = res[-digits:]
    return int(res)
