import json
import logging
import os


def debug_cache(file_dir):
    """ Decorator to read/write results of function to file when --debug_cache set or DEBUG_CACHE=1 in environment """

    def inner(func):

        def wrapper(*args, **kwargs):
            # ###### Move past this section only when --debug_cache set or DEBUG_CACHE=1 ############

            if os.environ.get("STAKETAX_DEBUG_CACHE") == "1":
                pass
            else:
                return func(*args, **kwargs)

            # ######################################################################################

            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

            debug_file = _debug_file_path(file_dir, args, func)

            # Debugging only: when --debug_cache flag set, read from cache file
            if os.path.exists(debug_file):
                with open(debug_file, "r") as f:
                    out = json.load(f)
                    logging.info("Loaded debug_file %s", debug_file)
                    return out

            result = func(*args, **kwargs)

            # Debugging only: when --debug_cache flat set, write to cache file
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

    path = os.path.join(file_dir, "debug.{}.json".format("-".join(fields_clean)))
    return path
