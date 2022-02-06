# Documentation
# https://docs.iotex.io/reference/node-core-api-grpc
# https://github.com/iotexproject/iotex-core
# https://github.com/iotexproject/iotex-explorer
from common.make_tx import make_reward_tx, make_transfer_in_tx, make_transfer_out_tx
from iotex import constants as co


def is_transfer_transaction(elem):
    return elem.get("action", {}).get("core", {}).get("transfer", False)


def is_staking_reward_transaction(elem):
    return elem.get("action", {}).get("core", {}).get("stakeAddDeposit", False)


def handle_transfer_transaction(wallet_address, elem, exporter, txinfo):
    core = elem["action"]["core"]
    transfer = core["transfer"]
    txreceiver = transfer["recipient"]
    transfer_amount = float(transfer["amount"]) / float(10 ** co.IOTEX_DECIMALS)

    row = None
    if wallet_address == txreceiver:
        row = make_transfer_in_tx(txinfo, transfer_amount, co.CURRENCY_IOTEX)
    else:
        fee_amount = (float(core["gasLimit"]) * float(core["gasPrice"])) / float(10 ** co.IOTEX_DECIMALS)
        txinfo.fee = fee_amount
        row = make_transfer_out_tx(txinfo, transfer_amount, co.CURRENCY_IOTEX, txreceiver)
    exporter.ingest_row(row)


def handle_staking_reward_transaction(elem, exporter, txinfo):
    core = elem["action"]["core"]
    deposit = core["stakeAddDeposit"]
    amount = float(deposit["amount"]) / float(10 ** co.IOTEX_DECIMALS)
    row = make_reward_tx(txinfo, amount, co.CURRENCY_IOTEX)
    exporter.ingest_row(row)
