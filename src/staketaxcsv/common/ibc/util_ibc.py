import logging

from requests import JSONDecodeError


def _ingest_rows(exporter, txinfo, msginfo, rows, comment):
    for i, row in enumerate(rows):
        row.comment = comment

        # Insert transaction fee for first csv row only
        if i == 0 and msginfo.msg_index == 0:
            row.fee = txinfo.fee
            row.fee_currency = txinfo.fee_currency
        else:
            row.fee = ""
            row.fee_currency = ""

        exporter.ingest_row(row)


def retry(max_retries: int = 5):
    def _inner1(method):
        def _inner2(self, *args, **kwargs):
            for i in range(max_retries):
                try:
                    return method.__call__(self, *args, **kwargs)
                except JSONDecodeError as exc:
                    logging.warning(f'Jsondecode error: {exc}. Retrying: {i + 1}')

            raise exc
        return _inner2
    return _inner1
