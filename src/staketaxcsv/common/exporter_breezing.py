"""
Exporter for Breezing (breezing.io) CSV format.

Breezing stores one row per token movement ("leg"), so a stake.tax transaction
becomes one or two CSV rows sharing the same transactionId:

  * direction is "in" or "out"; amount is signed (negative on "out" legs).
  * fee is negative and only allowed on "out" legs.  A receive-only transaction
    that paid a fee (e.g. gas on a reward claim) gets an extra fee-only "out" leg.
  * date is UTC "yyyy-MM-dd HH:mm:ss"; amountFiat/feeFiat of "0" means "not
    priced yet" (Breezing computes fiat values after import).
"""

import csv
import io
import logging
import re
from decimal import Decimal, InvalidOperation

from staketaxcsv.common import ExporterTypes as et

# Columns of Breezing's transaction CSV import (Breezing-CSV-Upload-Template.csv),
# plus informational addedVia/chain/note.
BREEZING_FIELDS = [
    "date",
    "transactionId",
    "direction",
    "walletFrom",
    "walletTo",
    "token",
    "feeToken",
    "amount",
    "fee",
    "type",
    "amountFiat",
    "feeFiat",
    "addedVia",
    "chain",
    "note",
]

_BREEZING_TYPES = {
    et.TX_TYPE_STAKING: "staking",
    et.TX_TYPE_AIRDROP: "airdrop",
    et.TX_TYPE_TRADE: "trade",
    et.TX_TYPE_INCOME: "income",
    et.TX_TYPE_SPEND: "spend",
    et.TX_TYPE_BORROW: "borrow",
    et.TX_TYPE_REPAY: "repay",
    et.TX_TYPE_LP_DEPOSIT: "lp_deposit",
    et.TX_TYPE_LP_WITHDRAW: "lp_withdraw",
    et.TX_TYPE_MARGIN_TRADE_FEE: "fee",
    et.TX_TYPE_REALIZED_PNL: "realized_pnl",
}

_BREEZING_CHAINS = {
    "SOL": "solana",
}

_FORMULA_TRIGGER = re.compile(r"[=+\-@\t\r]")
_NUM_CHARS = "\\d.,'\u0020\u00A0\u202F"
_NUMERIC_LIKE = re.compile(r"[+-]?[" + _NUM_CHARS + r"]*\d[" + _NUM_CHARS + r"]*(?:[eE][+-]?\d+)?")


def _sanitize_cell(value):
    if not isinstance(value, str) or value == "":
        return value
    if not _FORMULA_TRIGGER.match(value):
        return value
    if _NUMERIC_LIKE.fullmatch(value):
        return value
    return "'" + value


def _amount_str(amount):
    if amount is None:
        return ""
    s = str(amount).strip()
    if s == "":
        return ""
    try:
        d = Decimal(s)
    except InvalidOperation:
        return s
    if d == 0:
        return "0"
    return format(d.normalize(), "f")


def _negate(amount_str):
    if amount_str in ("", "0"):
        return amount_str
    if amount_str.startswith("-"):
        return amount_str[1:]
    return "-" + amount_str


def _clean_note(comment):
    if not comment:
        return ""
    return re.sub(r"(?:\r?\n|\r)+", " ", str(comment))


class ExporterBreezing:

    def __init__(self, wallet_address, ticker):
        self.wallet_address = wallet_address or ""
        self.chain = _BREEZING_CHAINS.get(ticker, ticker.lower()) if ticker else ""

    def export(self, rows, csvpath):
        legs = []
        for row in rows:
            legs.extend(self._legs_for_row(row))

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=BREEZING_FIELDS, lineterminator="\r\n")
        writer.writeheader()
        for leg in legs:
            writer.writerow({k: _sanitize_cell(v) for k, v in leg.items()})

        with open(csvpath, "w", newline="", encoding="utf-8") as f:
            f.write(buf.getvalue().rstrip("\r\n"))

        logging.info("Wrote to %s", csvpath)
        return csvpath

    def _legs_for_row(self, row):
        received = _amount_str(row.received_amount)
        sent = _amount_str(row.sent_amount)
        fee = _amount_str(row.fee)

        has_in = received not in ("", "0") and row.received_currency
        has_out = sent not in ("", "0") and row.sent_currency
        has_fee = fee not in ("", "0") and row.fee_currency

        tx_type = _BREEZING_TYPES.get(row.tx_type, row.tx_type.lower().lstrip("_"))

        legs = []
        if has_in and has_out:
            # Trade-like transaction: one "out" leg (carrying the fee) + one "in" leg.
            legs.append(self._leg(
                row, "out", row.sent_currency, _negate(sent),
                fee=_negate(fee) if has_fee else "0",
                fee_token=row.fee_currency if has_fee else row.sent_currency,
                tx_type=tx_type,
            ))
            legs.append(self._leg(row, "in", row.received_currency, received, tx_type=tx_type))
        elif has_in:
            if row.tx_type == et.TX_TYPE_TRANSFER:
                tx_type = "receive"
            legs.append(self._leg(row, "in", row.received_currency, received, tx_type=tx_type))
            if has_fee:
                # Fee cannot live on an "in" leg in Breezing; emit a fee-only "out" leg.
                legs.append(self._leg(
                    row, "out", row.fee_currency, "0",
                    fee=_negate(fee), fee_token=row.fee_currency, tx_type="fee",
                ))
        elif has_out:
            if row.tx_type == et.TX_TYPE_TRANSFER:
                tx_type = "send"
            legs.append(self._leg(
                row, "out", row.sent_currency, _negate(sent),
                fee=_negate(fee) if has_fee else "0",
                fee_token=row.fee_currency if has_fee else row.sent_currency,
                tx_type=tx_type,
            ))
        elif has_fee:
            # Fee-only transaction (failed tx, margin/funding fee, ...).
            legs.append(self._leg(
                row, "out", row.fee_currency, "0",
                fee=_negate(fee), fee_token=row.fee_currency, tx_type="fee",
            ))

        return legs

    def _leg(self, row, direction, token, amount, fee="0", fee_token="", tx_type=""):
        return {
            "date": row.timestamp,
            "transactionId": row.txid or "",
            "direction": direction,
            "walletFrom": self.wallet_address if direction == "out" else "",
            "walletTo": self.wallet_address if direction == "in" else "",
            "token": token,
            "feeToken": fee_token or token,
            "amount": amount,
            "fee": fee,
            "type": tx_type,
            "amountFiat": "0",
            "feeFiat": "0",
            "addedVia": "stake.tax",
            "chain": self.chain,
            "note": _clean_note(row.comment),
        }
