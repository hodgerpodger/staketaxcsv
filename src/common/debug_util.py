import json
import logging
import os


def use_debug_files(localconfig, file_dir):
    """ Decorator to read/write results of function to file (debug mode only) """

    def inner(func):

        def wrapper(*args, **kwargs):
            # ### Move past this section only when a debug variable is True #####################
            if localconfig is None:
                # Workaround when localconfig not available, can use localconfig=None such that:
                # Assumes class/instance method with self.debug or cls.debug is available.
                if hasattr(args[0], "debug") and args[0].debug:
                    pass
                else:
                    return func(*args, **kwargs)
            else:
                if localconfig.debug:
                    pass
                else:
                    return func(*args, **kwargs)
            # ####################################################################################

            debug_file = _debug_file_path(file_dir, args, func)

            # Debugging only: when --debug flag set, read from cache file
            if os.path.exists(debug_file):
                with open(debug_file, "r") as f:
                    out = json.load(f)
                    logging.info("Loaded debug_file %s", debug_file)
                    return out

            result = func(*args, **kwargs)

            # Debugging only: when --debug flat set, write to cache file
            with open(debug_file, "w") as f:
                json.dump(result, f, indent=4)
            logging.info("Wrote to %s for debugging", debug_file)

            return result

        return wrapper

    return inner


def _debug_file_path(file_dir, fields, func):
    fields_clean = list(fields[:])
    fields_clean[0] = func.__name__

    # Remove special symbols to create a file path
    fields_clean = [''.join(filter(str.isalnum, str(f))) for f in fields_clean]

    path = "{}/debug.{}.json".format(file_dir, "-".join(fields_clean))
    return path
