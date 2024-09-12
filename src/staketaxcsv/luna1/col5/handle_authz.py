import logging

from staketaxcsv.common.make_tx import make_reward_tx
from staketaxcsv.luna1 import util_terra
COIN_RECEIVED = "coin_received"
COIN_SPENT = "coin_spent"


def handle(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    transfers_in = _transfers_in_authz(elem, wallet_address)

    if len(transfers_in) > 0:
        pass
    else:
        raise Exception("Unexpected condition for handle_authz.handle()")

    # Sum rewards by currency
    rewards = {}
    for amount, currency in transfers_in:
        rewards[currency] = rewards.get(currency, 0) + float(amount)

    # Create rows for staking rewards
    i = 0
    for currency in sorted(rewards.keys()):
        amount = rewards[currency]
        if amount == 0:
            logging.info("Skipping reward=0 for currency=%s", currency)
            continue

        row = make_reward_tx(txinfo, amount, currency, txid, empty_fee=True)
        exporter.ingest_row(row)
        i += 1


def _transfers_in_authz(elem, wallet_address):
    transfers_in = []

    for log in elem["logs"]:
        for event in log["events"]:
            event_type, attributes = event["type"], event["attributes"]

            if event_type == COIN_RECEIVED:
                attributes = event["attributes"]

                for i in range(0, len(attributes), 3):
                    receiver, amount = None, None
                    for j in range(0, 3):
                        k = attributes[i + j]["key"]
                        v = attributes[i + j]["value"]

                        if k == "receiver":
                            receiver = v
                        if k == "amount":
                            amount = v

                    if receiver == wallet_address and amount:
                        for amt, cur in util_terra._amounts(amount):
                            transfers_in.append((amt, cur))

    return transfers_in
