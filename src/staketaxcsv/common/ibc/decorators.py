from functools import wraps
from staketaxcsv.common.ibc.denoms import IBCAddrs
from staketaxcsv import settings_csv


def set_ibc_cache():
    """
    Decorator: Runs IBCAddrs.set_cache() at end of function
    Should apply to txhistory() for all IBC-based reports.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the wrapped function
            result = func(*args, **kwargs)

            IBCAddrs.set_cache()

            # Return the result of the function
            return result

        return wrapper

    return decorator
