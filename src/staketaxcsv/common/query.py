import logging
import time
from requests.exceptions import JSONDecodeError, Timeout
REQUEST_TYPE_GET = "GET"
REQUEST_TYPE_POST = "POST"


def get_with_retries(session, url, params, headers, retries=4, backoff_factor=2):
    return _make_request_with_retries(
        REQUEST_TYPE_GET, session, url, params, headers, retries, backoff_factor)


def post_with_retries(session, url, data, headers, retries=3, backoff_factor=1):
    return _make_request_with_retries(
        REQUEST_TYPE_POST, session, url, data, headers, retries, backoff_factor)


def _make_request_with_retries(request_type, session, url, data, headers, retries, backoff_factor):
    for attempt in range(retries):
        try:
            if request_type == REQUEST_TYPE_GET:
                response = session.get(url, params=data, headers=headers)
            elif request_type == REQUEST_TYPE_POST:
                response = session.post(url, json=data, headers=headers)
            return response.json()  # Parse and return JSON here

        except (JSONDecodeError, Timeout, TimeoutError) as e:
            logging.warning(f"Error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                wait_time = backoff_factor * (2 ** attempt)
                logging.info(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                logging.error("Max retries reached. Unable to get a valid response.")
                raise

    raise Exception("Failed to fetch data after maximum retries.")
