import logging
import json
import os
from tests.settings_test import DATADIR


def mock_query_one_arg(func, arg1, dirname=""):
    args = [arg1]
    return _mock_query(func, args, dirname)


def mock_query_two_args(func, arg1, arg2, dirname=""):
    args = [arg1, arg2]
    return _mock_query(func, args, dirname)


def mock_query_three_args(func, arg1, arg2, arg3, dirname=""):
    args = [arg1, arg2, arg3]
    return _mock_query(func, args, dirname)


def mock_query_four_args(func, arg1, arg2, arg3, arg4, dirname=""):
    args = [arg1, arg2, arg3, arg4]
    return _mock_query(func, args, dirname)


def mock_query_five_args(func, arg1, arg2, arg3, arg4, arg5, dirname=""):
    args = [arg1, arg2, arg3, arg4, arg5]
    return _mock_query(func, args, dirname)


def mock_query_six_args(func, arg1, arg2, arg3, arg4, arg5, arg6, dirname=""):
    args = [arg1, arg2, arg3, arg4, arg5, arg6]
    return _mock_query(func, args, dirname)


def _mock_query(func, args, dirname=""):
    json_dir, json_path, = _create_filename(func, args, dirname)

    if not os.path.exists(json_path):
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        # Run the function
        data = func(*args)

        # Save result to local file
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info("Wrote to %s", json_path)

    logging.info("Loading mock query result from json=%s", json_path)
    with open(json_path, 'r') as f:
        result = json.load(f)
    return result


def _create_filename(func, args, dirname):
    # Determine file directory
    if dirname.startswith("/"):
        # If absolute path, use it.
        json_dir = dirname
    else:
        # If relative path, put in data directory for tests
        json_dir = DATADIR + "/" + (dirname if dirname else _clean(func.__name__))

    # Determine file path
    filename_parts = [_clean(func.__name__)] + [_clean(x) for x in args]
    json_path = json_dir + "/" + "-".join(filename_parts) + ".json"

    return json_dir, json_path


def _clean(arg):
    if type(arg) in (str, int, float):
        return str(arg).replace("/", "#").replace(" ", "#")
    else:
        return ""
