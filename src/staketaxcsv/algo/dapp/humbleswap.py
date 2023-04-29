import re

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import export_reward_tx, export_unknown
from staketaxcsv.algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_lp_add_group,
    is_lp_remove_group,
    is_swap_group,
)
from staketaxcsv.algo.transaction import get_transaction_note, get_transfer_asset, is_app_call, is_transfer
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

APPLICATION_ID_HUMBLESWAP_PROXY = 818079669

HUMBLESWAP_LP_TICKER = "HMBL2LT"

HUMBLESWAP_AMM_APPL_ARGS = set(["AA==", "Aw==", "AAAAAAAAAAA="])
HUMBLESWAP_FARM_APPL_ARGS = set(["AA==", "BA==", "AAAAAAAAAAA="])

HUMBLESWAP_TRANSACTION_PROXY_SWAP = "NS1KHQ=="

reach_pattern = re.compile(r"^Reach \d+\.\d+\.\d+$")


class HumbleSwap(Dapp):
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "HumbleSwap"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return self._is_humbleswap_amm_transaction(group) or self._is_humbleswap_farm_transaction(group)

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        txinfo.comment = self.name

        if is_swap_group(self.user_address, group):
            handle_swap(self.user_address, group, self.exporter, txinfo)
        elif is_lp_add_group(self.user_address, group):
            handle_lp_add(group, self.exporter, txinfo)
        elif is_lp_remove_group(self.user_address, group):
            handle_lp_remove(group, self.exporter, txinfo)
        elif self._is_humbleswap_farm_transaction(group):
            self._handle_humbleswap_farm(group, txinfo)
        else:
            export_unknown(self.exporter, txinfo)

    def _is_humbleswap_amm_transaction(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        # TODO fetch pool app ids from the protocol app (771884869) transactions
        transaction = group[-1]
        if not is_app_call(transaction):
            return False

        note = get_transaction_note(transaction)
        if not note:
            return False

        if not reach_pattern.match(note):
            return False

        appl_args = set(transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"])
        return bool(appl_args & HUMBLESWAP_AMM_APPL_ARGS)

    def _is_humbleswap_farm_transaction(self, group):
        if len(group) > 2:
            return False

        # TODO fetch farm app ids from the announcer app (830314595 and 857348615) transactions
        transaction = group[-1]
        if not is_app_call(transaction):
            return False

        note = get_transaction_note(transaction)
        if not note:
            return False

        if not reach_pattern.match(note):
            return False

        appl_args = set(transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"])
        return bool(appl_args & HUMBLESWAP_FARM_APPL_ARGS)

    def _handle_humbleswap_farm(self, group, txinfo):
        fee_amount = 0
        app_transaction = group[-1]

        inner_transactions = app_transaction.get("inner-txns", [])
        for transaction in inner_transactions:
            if is_transfer(transaction):
                reward = get_transfer_asset(transaction)
                if not reward.zero() and reward.ticker != HUMBLESWAP_LP_TICKER:
                    export_reward_tx(self.exporter, txinfo, reward, fee_amount)
