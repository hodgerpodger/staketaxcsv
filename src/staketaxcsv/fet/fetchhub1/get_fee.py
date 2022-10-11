"""
Note on get_fee():
if fetchcli exists: returns fee
if fetchcli does not exist: returns empty string
   (generally okay because fee is super tiny as to be neglible so instructions not provided)

fetchcli can be found at https://github.com/fetchai/fetchd/archive/refs/tags/v0.7.4.tar.gz
"""

import logging
import subprocess

import yaml
from staketaxcsv.fet.fetchhub1 import constants as co2


def get_fee(elem):
    try:
        return _get_fee(elem)
    except Exception as e:
        logging.info("get_fee() exception: %s", str(e))
        return ""


def _get_fee(elem):
    if not FetchCLI.exists():
        return ""

    tx_parsed = FetchCLI.decode_tx(elem["tx"])
    if not tx_parsed:
        return ""

    # Modify elem: add tx_parsed element
    elem["tx_parsed"] = tx_parsed

    # Extract fee
    amount_list = tx_parsed["fee"]["amount"]
    if not amount_list:
        return ""
    fee = float(amount_list[0]["amount"]) / co2.EXP18
    denom = amount_list[0]["denom"]
    if denom != "afet":
        raise Exception("get_fee(): unexpected denom={}".format(denom))

    return fee


class FetchCLI:

    is_available = None

    @classmethod
    def exists(cls):
        if cls.is_available is not None:
            return cls.is_available

        try:
            result = cls._cmd("fetchcli")
            if "fetchd" in result:
                cls.is_available = True
                return True
        except Exception as e:
            pass

        cls.is_available = False
        return False

    @classmethod
    def _cmd(cls, s):
        logging.info(s)
        return subprocess.getoutput(s)

    @classmethod
    def decode_tx(cls, s64):
        line = "fetchcli tx decode {}".format(s64)
        yaml_string = cls._cmd(line)
        if not yaml_string:
            return False

        try:
            json = yaml.safe_load(yaml_string)
            if json and "msg" in json:
                return json
        except Exception as e:
            pass

        return False
