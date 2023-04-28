
import base64
import string


def b64_decode_ascii(b64: str) -> str:
    try:
        decoded = base64.b64decode(b64).decode("ascii", "ignore")
    except Exception:
        return ""
    else:
        return "".join([s for s in decoded if s in string.printable])


def b64_decode_uint(b64: str) -> int:
    try:
        return int.from_bytes(base64.b64decode(b64), "big", signed=False)
    except Exception:
        return 0
