
import base64
import string


def b64_decode_ascii(b64: str) -> str:
    try:
        decoded = base64.b64decode(b64).decode("ascii", "ignore")
    except Exception:
        return ""
    else:
        return "".join([s for s in decoded if s in string.printable])
