from common.ibc.MsgInfoIBC import MsgInfoIBC
from luna2.api_lcd import Luna2LcdAPI
from luna2.config_luna2 import localconfig
from settings_csv import LUNA2_LCD_NODE


def _contract_address_to_currency(address):
    data = Luna2LcdAPI(LUNA2_LCD_NODE).contract_history(address)
    msg = _extract_msg(data)

    currency = msg["symbol"]
    decimals = int(msg["decimals"])

    return currency, decimals


def _extract_msg(data):
    for entry in data["entries"]:
        if entry["operation"] == "CONTRACT_CODE_HISTORY_OPERATION_TYPE_INIT":
            msg = entry["msg"]
            return msg

    return None


def asset_to_currency(amount_raw, asset):
    # example assets:
    # 'ibc/B3504E092456BA618CC28AC671A71FB08C6CA0FD0BE7C8A5B5A3E2DD933CC9E4'
    # 'terra1nsuqsk6kh58ulczatwev87ttq2z6r3pusulg9r24mfj2fvtzd4uq3exn26
    # 'uluna'

    if asset.startswith("terra"):
        currency, decimals = _contract_address_to_currency(asset)
        amount = float(amount_raw) / (10 ** decimals)
        return amount, currency
    else:
        return MsgInfoIBC.asset_to_currency(amount_raw, asset, LUNA2_LCD_NODE, localconfig.ibc_addresses)
