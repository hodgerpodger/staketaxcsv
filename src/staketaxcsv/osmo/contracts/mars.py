import json


def extract_message(msginfo):
    message = msginfo.message

    if "msg" in message:
        return message["msg"]
    elif "msg__@stringify" in message:
        return json.loads(message["msg__@stringify"])
    else:
        raise Exception("Unable to extract message")
