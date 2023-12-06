import logging
import json
import os
from tests.constants import DATADIR


def mock_query_one_arg(func, arg1, dirname=""):
    args = [arg1]
    return _mock_query(func, args, dirname)


def _mock_query(func, args, dirname=""):
    # Create a filename
    dir = DATADIR + "/" + _clean(dirname if dirname else func.__name__)
    filename_parts = [_clean(func.__name__)] + [_clean(x) for x in args]
    json_path = dir + "/" + "-".join(filename_parts)

    if not os.path.exists(json_path):
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Run the function
        data = func(*args)

        # Save result to local file
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info("Wrote to %s", json_path)

    with open(json_path, 'r') as f:
        result = json.load(f)
    return result


def _clean(arg):
    if type(arg) in (str, int, float):
        return str(arg).replace("/", "")
    else:
        return ""
