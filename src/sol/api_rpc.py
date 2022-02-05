import logging
import random
import time
from datetime import datetime

import requests
from settings_csv import SOL_NODE
from sol.constants import BILLION, PROGRAMID_STAKE, PROGRAMID_TOKEN_ACCOUNTS

TOKEN_ACCOUNTS = {}


class RpcAPI(object):

    @classmethod
    def _fetch(cls, method, params_list):
        myid = "be5adf2ee9f450f540cd7325740cdaea754ef660"
        data = {
            "method": method,
            "jsonrpc": "2.0",
            "params": params_list,
            "id": myid
        }
        headers = {}

        try:
            response = requests.post(SOL_NODE, json=data, headers=headers)

        except TimeoutError:
            # quicknode server sometimes refuses connection after hundreds of requests
            s = random.randint(60, 180)
            logging.warning("Returned timeout.  Sleeping %s seconds and retrying once...", s)
            time.sleep(s)
            response = requests.post(SOL_NODE, json=data, headers=headers)

        result = response.json()

        if "api.mainnet-beta.solana.com" in SOL_NODE:
            # mainnet: a bit slower to avoid rate-limiting errors
            time.sleep(0.3)
        else:
            time.sleep(0.1)

        return result

    @classmethod
    def _is_rate_limit_exceeded(cls, result):
        if "error" in result and "code" in result["error"] and result["error"]["code"] == 429:
            return True
        else:
            return False

    @classmethod
    def fetch_account(cls, address):
        params_list = [address, {"encoding": "jsonParsed"}]
        return cls._fetch("getAccountInfo", params_list)

    @classmethod
    def get_block_time(cls, block):
        params_list = [int(block)]
        data = cls._fetch("getBlockTime", params_list)

        ts = data["result"]
        date_string = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        return date_string

    @classmethod
    def get_block_rewards(cls, slot):
        params_list = [
            int(slot),
            {
                "encoding": "jsonParsed",
                "rewards": True
            }
        ]
        data = cls._fetch("getBlock", params_list)

        try:
            rewards = data["result"]["rewards"]
        except KeyError:
            return None

        out = []
        for reward in rewards:
            if reward["rewardType"] == "Staking":
                staking_address = reward["pubkey"]
                amount = reward["lamports"] / BILLION

                out.append((staking_address, amount))
        return out

    @classmethod
    def _get_inflation_reward(cls, staking_address, epoch):
        params_list = [
            [staking_address],
            {
                "epoch": epoch
            }
        ]
        data = cls._fetch("getInflationReward", params_list)
        return data

    @classmethod
    def get_inflation_reward(cls, staking_address, epoch):
        data = cls._get_inflation_reward(staking_address, epoch)

        if not data or "result" not in data:
            return None, None

        try:
            val = data["result"][0]
            if val:
                amount = val["amount"] / BILLION
                slot = val["effectiveSlot"]
                return amount, slot
        except KeyError:
            pass
        return None, None

    @classmethod
    def get_latest_epoch(cls):
        params_list = []
        data = cls._fetch("getEpochInfo", params_list)
        epoch = data["result"]["epoch"]
        return epoch

    @classmethod
    def fetch_staking_addresses(cls, wallet_address):
        data = cls._fetch_staking_addresses(wallet_address)

        if "result" not in data:
            return []

        addresses = [elem["pubkey"] for elem in data["result"]]
        return addresses

    @classmethod
    def _fetch_staking_addresses(cls, wallet_address):
        params_list = [
            PROGRAMID_STAKE,
            {
                "encoding": "jsonParsed",
                "filters": [
                    {
                        "memcmp": {
                            "offset": 12,
                            "bytes": wallet_address
                        }
                    }
                ]
            }
        ]
        return cls._fetch("getProgramAccounts", params_list)

    @classmethod
    def fetch_tx(cls, txid):
        params_list = [txid, {"encoding": "jsonParsed"}]
        return cls._fetch("getConfirmedTransaction", params_list)

    @classmethod
    def fetch_token_accounts(cls, wallet_address):
        if wallet_address in TOKEN_ACCOUNTS:
            return TOKEN_ACCOUNTS[wallet_address]

        data = cls._fetch_token_accounts(wallet_address)

        result = cls._extract_token_accounts(data["result"]["value"])
        TOKEN_ACCOUNTS[wallet_address] = result
        return result

    @classmethod
    def _fetch_token_accounts(cls, wallet_address):
        logging.info("Querying _fetch_token_accounts_()... wallet_address=%s", wallet_address)
        params_list = [
            wallet_address,
            {
                "programId": PROGRAMID_TOKEN_ACCOUNTS
            },
            {
                "encoding": "jsonParsed"
            }
        ]
        return cls._fetch("getTokenAccountsByOwner", params_list)

    @classmethod
    def _extract_token_accounts(cls, elems):
        out = {}
        for elem in elems:
            address = elem["pubkey"]
            info = elem["account"]["data"]["parsed"]["info"]
            mint = info["mint"]
            decimals = info["tokenAmount"]["decimals"]

            out[address] = {
                "mint": mint,
                "decimals": decimals
            }
        return out

    @classmethod
    def fetch_staking_accounts(cls, wallet_address):
        data = cls._fetch_staking_accounts(wallet_address)

        if "result" not in data:
            return []

        addresses = [elem["pubkey"] for elem in data["result"]]
        return addresses

    @classmethod
    def _fetch_staking_accounts(cls, wallet_address):
        logging.info("Querying _fetch_staking_accounts_()... wallet_address=%s", wallet_address)
        params_list = [
            PROGRAMID_STAKE,
            {
                "encoding": "jsonParsed",
                "filters" : [
                    {
                        "memcmp": {
                            "offset": 12,
                            "bytes": wallet_address
                        }
                    }
                ]
            }
        ]
        return cls._fetch("getProgramAccounts", params_list)

    @classmethod
    def get_txids(cls, wallet_address, limit=None, before=None):
        data = cls._get_txids(wallet_address, limit, before)

        if "result" not in data:
            return [], None

        # Extract txids
        out = []
        for info in data["result"]:
            if info["err"] is not None:
                continue
            if info["confirmationStatus"] != "finalized":
                continue

            txid = info["signature"]
            out.append(txid)

        # Extract last txid to use as "before" argument in subsequent query
        result_length = len(data["result"])
        if result_length == 1000 or (limit and result_length == limit):
            last_txid = data["result"][-1]["signature"]
        else:
            last_txid = None

        return out, last_txid

    @classmethod
    def _get_txids(cls, wallet_address, limit=None, before=None):
        config = {}
        if limit:
            config["limit"] = limit
        if before:
            config["before"] = before
        params_list = [
            wallet_address,
            config
        ]

        return cls._fetch("getConfirmedSignaturesForAddress2", params_list)

