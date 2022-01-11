import logging
from urllib.parse import urlencode, urlunparse

import requests

SCHEME = "https"


def _query_get(netloc, uri_path, query_params):
    url = urlunparse((
        SCHEME,
        netloc,
        uri_path,
        None,
        urlencode(query_params),
        None,
    ))

    logging.info("Querying url=%s...", url)
    response = requests.get(url)

    return response.json()
