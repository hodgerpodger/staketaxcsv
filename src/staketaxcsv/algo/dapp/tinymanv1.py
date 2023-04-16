from staketaxcsv.algo import constants as co
from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import (
    export_lp_deposit_tx,
    export_lp_withdraw_tx,
    export_participation_rewards,
    export_receive_tx,
    export_reward_tx,
    export_swap_tx,
    export_unknown,
)
from staketaxcsv.algo.transaction import get_transfer_asset, is_app_call
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

# For reference:
# https://github.com/tinymanorg/tinyman-py-sdk

APPLICATION_ID_TINYMAN_v10 = 350338509
APPLICATION_ID_TINYMAN_v11 = 552635992
APPLICATION_ID_TINYMAN_STAKING = 649588853

TINYMAN_TRANSACTION_SWAP = "c3dhcA=="           # "swap"
TINYMAN_TRANSACTION_REDEEM = "cmVkZWVt"         # "redeem"
TINYMAN_TRANSACTION_LP_ADD = "bWludA=="         # "mint"
TINYMAN_TRANSACTION_LP_REMOVE = "YnVybg=="      # "burn"
TINYMAN_TRANSACTION_CLAIM = "Y2xhaW0="          # "claim"


class TinymanV1(Dapp):
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "Tinyman v1"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return (self._is_tinyman_swap(group)
                    or self._is_tinyman_redeem(group)
                    or self._is_tinyman_lp_add(group)
                    or self._is_tinyman_lp_remove(group)
                    or self._is_tinyman_claim(group))

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        reward = Algo(group[0]["sender-rewards"])
        export_participation_rewards(reward, self.exporter, txinfo)

        if self._is_tinyman_swap(group):
            self._handle_tinyman_swap(group, txinfo)

        elif self._is_tinyman_redeem(group):
            self._handle_tinyman_redeem(group, txinfo)

        elif self._is_tinyman_lp_add(group):
            self._handle_tinyman_lp_add(group, txinfo)

        elif self._is_tinyman_lp_remove(group):
            self._handle_tinyman_lp_remove(group, txinfo)

        elif self._is_tinyman_claim(group):
            self._handle_tinyman_claim(group, txinfo)

        else:
            export_unknown(self.exporter, txinfo)

    def _is_tinyman_amm_transaction(self, group, required_length, appl_arg):
        if len(group) != required_length:
            return False

        return is_app_call(group[1], [APPLICATION_ID_TINYMAN_v10, APPLICATION_ID_TINYMAN_v11], appl_arg)

    def _is_tinyman_swap(self, group):
        return self._is_tinyman_amm_transaction(group, 4, TINYMAN_TRANSACTION_SWAP)

    def _is_tinyman_redeem(self, group):
        return self._is_tinyman_amm_transaction(group, 3, TINYMAN_TRANSACTION_REDEEM)

    def _is_tinyman_lp_add(self, group):
        return self._is_tinyman_amm_transaction(group, 5, TINYMAN_TRANSACTION_LP_ADD)

    def _is_tinyman_lp_remove(self, group):
        return self._is_tinyman_amm_transaction(group, 5, TINYMAN_TRANSACTION_LP_REMOVE)

    def _is_tinyman_claim(self, group):
        if len(group) != 2:
            return False

        return is_app_call(group[0], APPLICATION_ID_TINYMAN_STAKING, TINYMAN_TRANSACTION_CLAIM)

    def _handle_tinyman_swap(self, group, txinfo):
        fee_transaction = group[0]
        fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

        send_transaction = group[2]
        fee_amount += send_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)

        receive_transaction = group[3]
        receive_asset = get_transfer_asset(receive_transaction)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name)

    def _handle_tinyman_redeem(self, group, txinfo):
        fee_transaction = group[0]
        fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

        receive_transaction = group[2]
        receive_asset = get_transfer_asset(receive_transaction)

        export_receive_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name + " Redeem")

    def _handle_tinyman_lp_add(self, group, txinfo):
        fee_transaction = group[0]
        fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

        send_transaction = group[2]
        fee_amount += send_transaction["fee"]
        send_asset_1 = get_transfer_asset(send_transaction)

        send_transaction = group[3]
        fee_amount += send_transaction["fee"]
        send_asset_2 = get_transfer_asset(send_transaction)

        receive_transaction = group[4]
        lp_asset = get_transfer_asset(receive_transaction)

        export_lp_deposit_tx(
            self.exporter, txinfo, send_asset_1, send_asset_2, lp_asset, fee_amount, self.name)

    def _handle_tinyman_lp_remove(self, group, txinfo):
        fee_transaction = group[0]
        fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

        receive_transaction = group[2]
        receive_asset_1 = get_transfer_asset(receive_transaction)

        receive_transaction = group[3]
        receive_asset_2 = get_transfer_asset(receive_transaction)

        send_transaction = group[4]
        fee_amount += send_transaction["fee"]
        lp_asset = get_transfer_asset(send_transaction)

        export_lp_withdraw_tx(
            self.exporter, txinfo, lp_asset, receive_asset_1, receive_asset_2, fee_amount, self.name)

    def _handle_tinyman_claim(self, group, txinfo):
        app_transaction = group[0]
        fee_amount = app_transaction["fee"]

        receive_transaction = group[1]
        receive_asset = get_transfer_asset(receive_transaction)

        export_reward_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name)
