from functools import wraps
from staketaxcsv.common.ibc.denoms import IBCAddrs


def set_ibc_cache(localconfig):
    """ Decorator: Runs IBCAddrs.set_cache() at end of function if localconfig.cache is True.
        Generally should be used for all txhistory() of IBC-based reports.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the wrapped function
            result = func(*args, **kwargs)

            if getattr(localconfig, 'cache', False):
                IBCAddrs.set_cache()

            # Return the result of the function
            return result

        return wrapper

    return decorator
