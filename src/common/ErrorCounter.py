import logging


class ErrorCounter:

    errors = {}

    @classmethod
    def increment(cls, error_type, txid):
        cls.errors[error_type] = cls.errors.get(error_type, 0) + 1

        logging.error("Unable to handle txid=%s with error_type=%s", txid, error_type)

    @classmethod
    def log(cls, ticker, wallet_address):
        if len(cls.errors) > 0:
            data = {
                "ticker": ticker,
                "wallet_address": wallet_address,
                "error_count": cls.errors,
                "RLOG": 1,
                "event": "job_error_count"
            }
            logging.info(data)
