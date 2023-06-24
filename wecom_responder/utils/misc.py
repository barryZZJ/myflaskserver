import hashlib


def split_text(text: str, max_bytes: int) -> list[str]:
    chunks = []
    current_chunk = ""
    current_bytes = 0

    for char in text:
        char_bytes = char.encode('utf-8')
        if current_bytes + len(char_bytes) > max_bytes:
            chunks.append(current_chunk)
            current_chunk = ""
            current_bytes = 0

        current_chunk += char
        current_bytes += len(char_bytes)

    if current_bytes > 0:
        chunks.append(current_chunk)

    return chunks


def md5int(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)
