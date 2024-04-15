import json
import logging
import os
from staketaxcsv.common.ibc.api_lcd_v1 import LcdAPI_v1
import staketaxcsv.common.ibc.constants as co
from staketaxcsv.common.Cache import Cache
from staketaxcsv import settings_csv

# downloaded from https://raw.githubusercontent.com/PulsarDefi/IBC-Token-Data-Cosmos/main/native_token_data.json
PULSAR_DATA = os.path.dirname(os.path.realpath(__file__)) + "/pulsar_data.json"


class IBCAddrs:

    # Add hard-coded denoms only if lcd api lookup non-functional
    # <ibc_address> -> <denom>
    addrs = {
        "ibc/ED07A3391A112B175915CD8FAF43A2DA8E4790EDE12566649D0C2F97716B8518": "uosmo",
        "ibc/E6931F78057F7CC5DA0FD6CEF82FF39373A6E0452BF1FD76910B93292CF356C1": co.CUR_CRO,
        "ibc/8318B7E036E50C0CF799848F23ED84778AAA8749D9C0BCD4FF3F4AF73C53387F": "uloop",
    }

    loaded = False

    @classmethod
    def ibc_address_to_denom(cls, node, ibc_address):
        cls._load_cache()
        if ibc_address in IBCAddrs.addrs:
            return IBCAddrs.addrs[ibc_address]
        if not node:
            return None

        denom = LcdAPI_v1(node).ibc_address_to_denom(ibc_address)

        IBCAddrs.addrs[ibc_address] = denom
        return denom

    @classmethod
    def _load_cache(cls):
        if not settings_csv.DB_CACHE:
            return

        if not IBCAddrs.loaded:
            # Load IBC.addrs
            addrs_cache = Cache().get_ibc_addresses()
            IBCAddrs.addrs.update(addrs_cache)
            IBCAddrs.loaded = True
            logging.info("Loaded cache into IBCAddrs.addrs ...")

    @classmethod
    def set_cache(cls):
        if not settings_csv.DB_CACHE:
            return

        if IBCAddrs.loaded:
            Cache().set_ibc_addresses(IBCAddrs.addrs)
            logging.info("Set cache using IBCAddrs.addrs ...")


class PulsarData:

    loaded = False
    denoms = {}

    @classmethod
    def _load(cls):
        if not cls.loaded:
            with open(PULSAR_DATA, 'r') as f:
                # Parse the JSON file and convert it into a Python dictionary
                data = json.load(f)

                for s, val in data.items():
                    # i.e. erc20/0x2Cbea61fdfDFA520Ee99700F104D5b75ADf50B0c__acrechain
                    # i.e. factory/neutron1p8d89wvxyjcnawmgw72klknr3lg9gwwl6ypxda/newt__neutron
                    denom, _ = s.split("__")
                    cls.denoms[denom] = {
                        "symbol": val["symbol"],
                        "decimals": val["decimals"]
                    }

            cls.loaded = True

    @classmethod
    def has_denom(cls, denom):
        cls._load()

        return denom in cls.denoms

    @classmethod
    def denom_to_symbol(cls, denom):
        cls._load()

        if denom in cls.denoms:
            symbol = cls.denoms[denom]["symbol"]
            decimals = cls.denoms[denom]["decimals"]
            return symbol, decimals
        else:
            return None, None


def amount_currency_from_raw(amount_raw, currency_raw, lcd_node):
    # example currency_raw:
    # 'ibc/B3504E092456BA618CC28AC671A71FB08C6CA0FD0BE7C8A5B5A3E2DD933CC9E4'
    # 'uluna'
    # 'aevmos'
    if currency_raw is None:
        return amount_raw, currency_raw
    elif currency_raw.startswith("ibc/"):
        # ibc address
        denom = None
        try:
            denom = IBCAddrs.ibc_address_to_denom(lcd_node, currency_raw)
            amount, currency = _amount_currency_convert(amount_raw, denom)
            return amount, currency
        except Exception as e:
            logging.warning("Unable to find symbol for ibc address %s, denom=%s, exception=%s",
                            currency_raw, denom, str(e))
            amount = float(amount_raw) / co.MILLION
            currency = "unknown_{}".format(denom if denom else currency_raw)
            return amount, currency
    else:
        return _amount_currency_convert(amount_raw, currency_raw)


def _amount_currency_convert(amount_raw, currency_raw):
    # Special cases for nonconforming denoms/assets
    # currency_raw -> (currency, exponent)
    CURRENCY_RAW_MAP = {
        co.CUR_CRO: (co.CUR_CRO, 8),
        co.CUR_MOBX: (co.CUR_MOBX, 9),
        "gravity0xfB5c6815cA3AC72Ce9F5006869AE67f18bF77006": (co.CUR_PSTAKE, 18),
        "inj": (co.CUR_INJ, 18),
        "OSMO": (co.CUR_OSMO, 6),
        "osmo": (co.CUR_OSMO, 6),
        "rowan": ("ROWAN", 18),
        "basecro": (co.CUR_CRO, 8),
        "uusd": (co.CUR_USTC, 6),
        "factory/osmo1pfyxruwvtwk00y8z06dh2lqjdj82ldvy74wzm3/WOSMO": (co.CUR_WOSMO, 6),
        "peggy0xdAC17F958D2ee523a2206206994597C13D831ec7": (co.CUR_USDT, 6),
        "cw20:terra1lxx40s29qvkrcj8fsa3yzyehy7w50umdvvnls2r830rys6lu2zns63eelv": (co.CUR_ROAR, 6),
        "cw20:terra1nsuqsk6kh58ulczatwev87ttq2z6r3pusulg9r24mfj2fvtzd4uq3exn26": (co.CUR_ASTRO, 6),
        "erc20/0xAE6D3334989a22A65228732446731438672418F2": (co.CUR_CNTO, 18),
    }

    if currency_raw in CURRENCY_RAW_MAP:
        currency, exponent = CURRENCY_RAW_MAP[currency_raw]
        amount = float(amount_raw) / float(10 ** exponent)
        return amount, currency
    elif currency_raw.startswith("gamm/"):
        # osmosis lp currencies
        # i.e. "gamm/pool/6" -> "GAMM-6"
        amount = float(amount_raw) / co.EXP18
        _, _, num = currency_raw.split("/")
        currency = "GAMM-{}".format(num)
        return amount, currency
    elif currency_raw.endswith("-wei"):
        amount = float(amount_raw) / co.EXP18
        currency, _ = currency_raw.split("-wei")
        currency = currency.upper()
        return amount, currency
    elif currency_raw.startswith("a"):
        amount = float(amount_raw) / co.EXP18
        currency = currency_raw[1:].upper()
        return amount, currency
    elif currency_raw.startswith("nano"):
        amount = float(amount_raw) / co.EXP9
        currency = currency_raw[4:].upper()
        return amount, currency
    elif currency_raw.startswith("n"):
        amount = float(amount_raw) / co.EXP9
        currency = currency_raw[1:].upper()
        return amount, currency
    elif currency_raw.startswith("u"):
        amount = float(amount_raw) / co.MILLION
        currency = currency_raw[1:].upper()
        return amount, currency
    elif currency_raw.startswith("st"):
        # i.e. stinj, stujuno, staevmos
        amt, cur = _amount_currency_convert(amount_raw, currency_raw[2:])
        return amt, "st" + cur
    elif PulsarData.has_denom(currency_raw):
        currency, decimals = PulsarData.denom_to_symbol(currency_raw)
        amount = float(amount_raw) / (10**decimals)
        return amount, currency
    else:
        logging.error("_amount_currency_from_raw(): no case for amount_raw={}, currency_raw={}".format(
            amount_raw, currency_raw))
        amount = float(amount_raw) / co.MILLION
        currency = "unknown_{}".format(currency_raw)
        return amount, currency
