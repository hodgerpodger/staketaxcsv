import logging
import time
from datetime import datetime, timezone
import requests

from staketaxcsv.common.query import post_with_retries
from staketaxcsv.common.debug_util import debug_cache
from staketaxcsv.settings_csv import REPORTS_DIR, SOL_NODE
from staketaxcsv.sol.config_sol import localconfig
from staketaxcsv.sol.constants import BILLION, PROGRAMID_STAKE, PROGRAMID_TOKEN_ACCOUNTS, PROGRAMID_TOKEN_2022
TOKEN_ACCOUNTS = {}


class RpcAPI(object):
    session = requests.Session()

    @classmethod
    def _fetch(cls, method, params_list):
        myid = "be5adf2ee9f450f540cd7325740cdaea754ef660"
        data = {
            "method": method,
            "jsonrpc": "2.0",
            "params": params_list,
            "id": myid
        }

        result = post_with_retries(cls.session, SOL_NODE, data, {}, retries=5, backoff_factor=5)

        if "api.mainnet-beta.solana.com" in SOL_NODE:
            time.sleep(0.3)
        else:
            time.sleep(0.1)

        return result

    @classmethod
    def _fetch_with_retries(cls, method, params_list, retries=10, backoff_factor=0.2):
        for i in range(retries):
            data = cls._fetch(method, params_list)

            if "result" in data:
                break
            logging.info("no result in method=%s, params_list=%s.  retrying i=%s....",
                         method, params_list, i)
            logging.info("data: %s", data)
            time.sleep(backoff_factor * i)

        return data

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
                "rewards": True,
                "maxSupportedTransactionVersion": 64,  # just choosing accepted high number
            }
        ]

        data = cls._fetch_with_retries("getBlock", params_list, retries=40, backoff_factor=1)

        try:
            rewards = data["result"]["rewards"]
        except KeyError:
            logging.error("Unknown result in rpc method getBlock")
            logging.error("data:%s", data)

            return None

        out = []
        for reward in rewards:
            if reward["rewardType"] == "Staking":
                staking_address = reward["pubkey"]
                amount = reward["lamports"] / BILLION

                out.append((staking_address, amount))
        return out

    @classmethod
    @debug_cache(REPORTS_DIR)
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

        logging.info("rpc get_inflation_reward for staking_address=%s, epoch=%s:", staking_address, epoch)
        logging.info(data)

        # Throttled at 1 req/sec, I think at rpc api level, but a tad unsure.
        time.sleep(1)

        if not data or "result" not in data:
            return None

        try:
            val = data["result"][0]
            if val:
                amount = val["amount"] / BILLION
                return amount
        except KeyError:
            pass
        return None

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
    @debug_cache(REPORTS_DIR)
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
    @debug_cache(REPORTS_DIR)
    def fetch_tx(cls, txid):
        params_list = [txid, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
        return cls._fetch("getTransaction", params_list)

    @classmethod
    def fetch_token_accounts(cls, wallet_address):
        if wallet_address in TOKEN_ACCOUNTS:
            return TOKEN_ACCOUNTS[wallet_address]

        data = cls._fetch_token_accounts(wallet_address, PROGRAMID_TOKEN_ACCOUNTS)
        data2 = cls._fetch_token_accounts(wallet_address, PROGRAMID_TOKEN_2022)

        result = {}
        result.update(cls._extract_token_accounts(data["result"]["value"]))
        result.update(cls._extract_token_accounts(data2["result"]["value"]))

        TOKEN_ACCOUNTS[wallet_address] = result
        return result

    @classmethod
    @debug_cache(REPORTS_DIR)
    def _fetch_token_accounts(cls, wallet_address, program_id):
        logging.info("Querying _fetch_token_accounts_()... wallet_address=%s, program_id=%s",
                     wallet_address, program_id)
        params_list = [
            wallet_address,
            {
                "programId": program_id
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
    def get_txids(cls, wallet_address, limit=None, before_txid=None):
        exclude_failed = localconfig.exclude_failed

        data = cls._get_txids(wallet_address, limit, before_txid)

        if "result" not in data or data["result"] is None:
            return [], None

        # Extract txids
        out = []
        for info in data["result"]:
            if "signature" not in info:
                continue
            if info["confirmationStatus"] != "finalized":
                continue

            # Omit failed transactions if exclude_failed setting is on.
            if exclude_failed:
                if info.get("err") is not None:
                    continue

            txid = info["signature"]
            block_time = info["blockTime"]

            out.append((txid, block_time))

        # Determine "before_txid" argument in subsequent query: use last txid of this query
        if data["result"]:
            last_txid = data["result"][-1]["signature"]
        else:
            last_txid = None

        return out, last_txid

    @classmethod
    @debug_cache(REPORTS_DIR)
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

        return cls._fetch("getSignaturesForAddress", params_list)
