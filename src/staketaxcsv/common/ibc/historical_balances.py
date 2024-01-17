from staketaxcsv.common.ibc.api_mintscan_v1 import get_balances_all
from staketaxcsv.common.ExporterBalances import ExporterBalance
from collections import defaultdict
from dateutil import parser


def via_mintscan(native_denom, ticker, address, max_txs, start_date=None, end_date=None):
    entries = get_balances_all(ticker, address, max_txs, start_date, end_date)

    exporter = ExporterBalance(address)

    for entry in entries:
        timestamp = parser.parse(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        balance = defaultdict(int)

        # Process "bank" section
        for item in entry["bank"]:
            denom = item["denom"]
            amount = int(item["amount"])
            balance[denom] += amount

        # Process "delegation" section
        for item in entry["delegation"]:
            denom = item["balance"]["denom"]
            amount = int(item["balance"]["amount"])
            balance[denom] += amount

        # Process "unbonding" section
        for item in entry["unbonding"]:
            for subitem in item["entries"]:
                denom = native_denom
                amount = int(subitem["balance"])
                balance[denom] += amount

        # Ingest the summed balances into the exporter
        exporter.ingest_row(timestamp, dict(balance))

    return exporter
