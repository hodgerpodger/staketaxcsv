import logging
from urllib.parse import urlencode, urlunparse

import requests

SCHEME = "https"


class APIUtil:
    session = requests.Session()

    @classmethod
    def query_get(cls, netloc, uri_path, query_params):
        url = urlunparse((
            SCHEME,
            netloc,
            uri_path,
            None,
            urlencode(query_params),
            None,
        ))

        logging.info("Querying url=%s...", url)
        response = cls.session.get(url)

        return response.json()
