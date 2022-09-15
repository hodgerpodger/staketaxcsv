from staketaxcsv.common.ibc.api_lcd_cosmwasm import CosmWasmLcdAPI, extract_msg
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.luna2.config_luna2 import localconfig
from staketaxcsv.luna2.constants import MILLION
from staketaxcsv.settings_csv import LUNA2_LCD_NODE


def _contract_address_to_currency(address):
    if address in localconfig.currency_addresses:
        currency, decimals = localconfig.currency_addresses[address]
        return currency, int(decimals)

    data = CosmWasmLcdAPI(LUNA2_LCD_NODE).contract_history(address)
    msg = extract_msg(data)

    currency = msg["symbol"]
    decimals = int(msg["decimals"])

    localconfig.currency_addresses[address] = (currency, decimals)
    return currency, decimals


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
        return MsgInfoIBC.amount_currency_from_raw(amount_raw, asset, LUNA2_LCD_NODE, localconfig.ibc_addresses)


def amount_assets_to_currency(amount_assets_raw):
    # example amount_asset_raw:
    # '499591120uluna, 1308906268ibc/B3504E092456BA618CC28AC671A71FB08C6CA0FD0BE7C8A5B5A3E2DD933CC9E4'
    out = []
    for amount_asset_raw in amount_assets_raw.split(","):
        # Convert '499591120uluna' to ('499591120', 'uluna')
        amount_asset_raw = amount_asset_raw.strip()
        amount_raw, asset = _split_amount_asset(amount_asset_raw)

        amount, currency = asset_to_currency(amount_raw, asset)

        out.append((amount, currency))
    return out


def _split_amount_asset(amount_asset_raw):
    numbers = set("0123456789")
    index = 0
    while amount_asset_raw[index] in numbers:
        index += 1

    return amount_asset_raw[:index], amount_asset_raw[index:]


def lp_asset_to_currency(amount_raw, lp_asset):
    # example lp_asset:
    # terra1fd68ah02gr2y8ze7tm9te7m70zlmc7vjyyhs6xlhsdmqqcjud4dql4wpxr
    lp_currency = _lp_asset_to_currency(lp_asset)
    amount = float(amount_raw) / MILLION
    return amount, lp_currency


def _lp_asset_to_currency(lp_asset):
    if lp_asset in localconfig.lp_currency_addresses:
        return localconfig.lp_currency_addresses[lp_asset]

    data = CosmWasmLcdAPI(LUNA2_LCD_NODE).contract_history(lp_asset)
    msg = extract_msg(data)

    # Extract pair of currencies in LP pair
    if "asset_infos" in msg:
        currency1 = _asset_info_to_currency(msg["asset_infos"][0])
        currency2 = _asset_info_to_currency(msg["asset_infos"][1])
    elif "mint" in msg:
        minter = msg["mint"]["minter"]
        data = CosmWasmLcdAPI(LUNA2_LCD_NODE).contract_history(minter)
        msg = extract_msg(data)
        currency1 = _asset_info_to_currency(msg["asset_infos"][0])
        currency2 = _asset_info_to_currency(msg["asset_infos"][1])
    else:
        raise Exception("lp_asset_to_currency(): Unexpected msg: {}".format(msg))

    # alphabetic sort name
    if currency1 < currency2:
        lp_currency = "LP_{}_{}".format(currency1, currency2)
    else:
        lp_currency = "LP_{}_{}".format(currency2, currency1)

    localconfig.lp_currency_addresses[lp_asset] = lp_currency
    return lp_currency


def _asset_info_to_currency(asset_info):
    if "native_token" in asset_info:
        denom = asset_info["native_token"]["denom"]
        _, currency = asset_to_currency(0, denom)
        return currency
    elif "token" in asset_info:
        contract_addr = asset_info["token"]["contract_addr"]
        currency, _ = _contract_address_to_currency(contract_addr)
        return currency
    else:
        raise Exception("_asset_info_to_currency(): Unexpected asset_info: {}".format(asset_info))
