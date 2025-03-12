from functools import partial

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import (
    export_lp_deposit_tx,
    export_lp_withdraw_tx,
    export_reward_tx,
    export_stake_tx,
    export_unknown,
    export_unstake_tx,
)
from staketaxcsv.algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_lp_add_group,
    is_lp_remove_group,
    is_swap_group
)
from staketaxcsv.algo.transaction import (
    generate_inner_transfer_assets,
    get_fee_amount,
    get_inner_transfer_asset,
    get_inner_transfer_count,
    get_transfer_asset,
    get_transfer_receiver,
    is_app_call,
    is_asa_transfer,
    is_asset_optin,
    is_transfer,
    is_transfer_receiver,
    is_transaction_sender
)
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

# For reference:
# https://github.com/tinymanorg/tinyman-py-sdk

APPLICATION_ID_TINYMANV2_VALIDATOR = 1002541853
APPLICATION_ID_TINYMANV2_FOLKS_WRAPPER = 1385499515
APPLICATION_ID_TINYMANV2_STAKING = 649588853
APPLICATION_ID_TINYMANV2_GOVERNANCE_VAULT = 2200606875
APPLICATION_ID_TINYMANV2_GOVERNANCE_REWARDS = 2200608153

TINYMANV2_TRANSACTION_SWAP = "c3dhcA=="                                       # "swap"
TINYMANV2_TRANSACTION_ADD_LIQUIDITY = "YWRkX2xpcXVpZGl0eQ=="                  # "add_liquidity"
TINYMANV2_TRANSACTION_ADD_INITIAL_LIQUIDITY = "YWRkX2luaXRpYWxfbGlxdWlkaXR5"  # "add_initial_liquidity"
TINYMANV2_TRANSACTION_ADD_LIQUIDITY_FLEXIBLE = "ZmxleGlibGU="                 # "flexible"
TINYMANV2_TRANSACTION_ADD_LIQUIDITY_SINGLE = "c2luZ2xl"                       # "single"
TINYMANV2_TRANSACTION_REMOVE_LIQUIDITY = "cmVtb3ZlX2xpcXVpZGl0eQ=="           # "remove_liquidity"
TINYMANV2_TRANSACTION_NOOP = "bm9vcA=="                                       # "noop"
TINYMANV2_TRANSACTION_STAKING_COMMIT = "Y29tbWl0"                             # "commit"
TINYMANV2_TRANSACTION_GOVERNANCE_CREATE_LOCK = "Y3JlYXRlX2xvY2s="             # "create_lock"
TINYMANV2_TRANSACTION_GOVERNANCE_WITHDRAW = "d2l0aGRyYXc="                    # "withdraw"
TINYMANV2_TRANSACTION_GOVERNANCE_CLAIM_REWARDS = "Y2xhaW1fcmV3YXJkcw=="       # "claim_rewards"
TINYMANV2_TRANSACTION_INCREASE_BUDGET = "aW5jcmVhc2VfYnVkZ2V0"                # "increase_budget"


class TinymanV2(Dapp):
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "Tinyman v2"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return (self._is_tinymanv2_swap(group)
                    or self._is_tinymanv2_lp_add(group)
                    or self._is_tinymanv2_lp_add_single(group)
                    or self._is_tinymanv2_lending_lp_add(group)
                    or self._is_tinymanv2_lp_remove(group)
                    or self._is_tinymanv2_lp_remove_single(group)
                    or self._is_tinymanv2_lending_lp_remove(group)
                    or self._is_tinymanv2_staking_commit(group)
                    or self._is_tinymanv2_governance_create_lock(group)
                    or self._is_tinymanv2_governance_withdraw(group)
                    or self._is_tinymanv2_governance_claim_rewards(group))

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        txinfo.comment = self.name

        if self._is_tinymanv2_swap(group):
            handle_swap(self.user_address, group, self.exporter, txinfo)

        elif self._is_tinymanv2_lp_add(group):
            handle_lp_add(group, self.exporter, txinfo)

        elif self._is_tinymanv2_lp_add_single(group):
            self._handle_tinymanv2_lp_add_single(group, txinfo)

        elif self._is_tinymanv2_lending_lp_add(group):
            self._handle_tinymanv2_lending_lp_add(group, txinfo)

        elif self._is_tinymanv2_lp_remove(group):
            handle_lp_remove(group, self.exporter, txinfo)

        elif self._is_tinymanv2_lp_remove_single(group):
            self._handle_tinymanv2_lp_remove_single(group, txinfo)

        elif self._is_tinymanv2_lending_lp_remove(group):
            self._handle_tinymanv2_lending_lp_remove(group, txinfo)

        elif self._is_tinymanv2_staking_commit(group):
            pass

        elif self._is_tinymanv2_governance_create_lock(group):
            self._handle_tinymanv2_governance_create_lock(group, txinfo)

        elif self._is_tinymanv2_governance_withdraw(group):
            self._handle_tinymanv2_governance_withdraw(group, txinfo)

        elif self._is_tinymanv2_governance_claim_rewards(group):
            self._handle_tinymanv2_governance_claim_rewards(group, txinfo)

        else:
            export_unknown(self.exporter, txinfo)

    def _is_tinymanv2_swap(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        if not is_swap_group(self.user_address, group):
            return False

        transaction = group[-1]
        if is_transfer(transaction):
            if get_transfer_receiver(transaction) != co.ADDRESS_PERA:
                return False
            transaction = group[-2]

        return is_app_call(transaction, APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_SWAP)

    def _is_tinymanv2_lp_add(self, group):
        if not is_lp_add_group(self.user_address, group):
            return False

        return is_app_call(group[-1],
                        APPLICATION_ID_TINYMANV2_VALIDATOR,
                        [TINYMANV2_TRANSACTION_ADD_LIQUIDITY, TINYMANV2_TRANSACTION_ADD_INITIAL_LIQUIDITY])

    def _is_tinymanv2_lp_add_single(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        transaction = group[i]
        if not is_transfer(transaction):
            return False

        if not is_transaction_sender(self.user_address, transaction):
            return False

        i += 1
        if i == length:
            return False

        transaction = group[i]
        if not is_app_call(transaction, APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_ADD_LIQUIDITY):
            return False

        return is_app_call(transaction, APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_ADD_LIQUIDITY_SINGLE)

    def _is_tinymanv2_lending_lp_add(self, group):
        length = len(group)
        if length < 4 or length > 5:
            return False

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        for j in range(2):
            transaction = group[i + j]
            if not is_transfer(transaction):
                return False

            if not is_transaction_sender(self.user_address, transaction):
                return False

        if not is_app_call(group[-2], APPLICATION_ID_TINYMANV2_FOLKS_WRAPPER, TINYMANV2_TRANSACTION_ADD_LIQUIDITY):
            return False

        return is_app_call(group[-1], APPLICATION_ID_TINYMANV2_FOLKS_WRAPPER, TINYMANV2_TRANSACTION_NOOP)

    def _is_tinymanv2_lp_remove(self, group):
        if not is_lp_remove_group(self.user_address, group):
            return False

        return is_app_call(group[-1], APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_REMOVE_LIQUIDITY)

    def _is_tinymanv2_lp_remove_single(self, group):
        length = len(group)
        if length < 2 or length > 4:
            return False

        i = 0
        while i < length and is_asset_optin(group[i]):
            i += 1

        if i == length:
            return False

        transaction = group[i]
        if not is_transfer(transaction):
            return False

        if not is_transaction_sender(self.user_address, transaction):
            return False

        send_asset = get_transfer_asset(transaction)
        if not send_asset.is_lp_token():
            return False

        transaction = group[-1]
        if not is_app_call(transaction, APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_REMOVE_LIQUIDITY):
            return False

        return get_inner_transfer_count(transaction) == 1

    def _is_tinymanv2_lending_lp_remove(self, group):
        length = len(group)
        if length < 3 or length > 5:
            return False

        i = 0
        while i < length and is_asset_optin(group[i]):
            i += 1

        transaction = group[i]
        if not is_transfer(transaction):
            return False

        if not is_transaction_sender(self.user_address, transaction):
            return False

        send_asset = get_transfer_asset(transaction)
        if not send_asset.is_lp_token():
            return False

        if not is_app_call(group[-2], APPLICATION_ID_TINYMANV2_FOLKS_WRAPPER, TINYMANV2_TRANSACTION_REMOVE_LIQUIDITY):
            return False

        return is_app_call(group[-1], APPLICATION_ID_TINYMANV2_FOLKS_WRAPPER, TINYMANV2_TRANSACTION_NOOP)

    def _is_tinymanv2_staking_commit(self, group):
        if len(group) != 1:
            return False

        return is_app_call(group[0], APPLICATION_ID_TINYMANV2_STAKING, TINYMANV2_TRANSACTION_STAKING_COMMIT)

    def _is_tinymanv2_governance_create_lock(self, group):
        length = len(group)
        if length < 3 or length > 4:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_TINYMANV2_GOVERNANCE_VAULT, TINYMANV2_TRANSACTION_INCREASE_BUDGET):
            return False

        if not is_app_call(group[-2], APPLICATION_ID_TINYMANV2_GOVERNANCE_VAULT, TINYMANV2_TRANSACTION_GOVERNANCE_CREATE_LOCK):
            return False

        return is_asa_transfer(group[-3])

    def _is_tinymanv2_governance_withdraw(self, group):
        if len(group) != 1:
            return False

        return is_app_call(group[0], APPLICATION_ID_TINYMANV2_GOVERNANCE_VAULT, TINYMANV2_TRANSACTION_GOVERNANCE_WITHDRAW)

    def _is_tinymanv2_governance_claim_rewards(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_TINYMANV2_GOVERNANCE_REWARDS, TINYMANV2_TRANSACTION_GOVERNANCE_CLAIM_REWARDS):
            return False

        return is_app_call(group[-2], APPLICATION_ID_TINYMANV2_GOVERNANCE_REWARDS, TINYMANV2_TRANSACTION_INCREASE_BUDGET)

    def _handle_tinymanv2_lp_add_single(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        send_transaction = group[i]
        send_asset = get_transfer_asset(send_transaction)

        app_transaction = group[i + 1]
        lp_asset = get_inner_transfer_asset(app_transaction,
                                            filter=partial(is_transfer_receiver, self.user_address))
        export_lp_deposit_tx(self.exporter, txinfo, send_asset, None, lp_asset, fee_amount)

    def _handle_tinymanv2_lp_remove_single(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        i = 0
        while is_asset_optin(group[i]):
            i += 1

        send_transaction = group[i]
        lp_asset = get_transfer_asset(send_transaction)

        app_transaction = group[i + 1]
        receive_asset = get_inner_transfer_asset(app_transaction,
                                                filter=partial(is_transfer_receiver, self.user_address))
        export_lp_withdraw_tx(self.exporter, txinfo, lp_asset, receive_asset, None, fee_amount)

    def _handle_tinymanv2_lending_lp_add(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset_1 = get_transfer_asset(group[-4])
        send_asset_2 = get_transfer_asset(group[-3])

        lp_asset = get_inner_transfer_asset(group[-2],
                                            filter=partial(is_transfer_receiver, self.user_address))

        export_lp_deposit_tx(self.exporter, txinfo, send_asset_1, send_asset_2, lp_asset, fee_amount, self.name)

    def _handle_tinymanv2_lending_lp_remove(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        lp_asset = get_transfer_asset(group[-3])

        receive_assets = list(generate_inner_transfer_assets(group[-2],
                                                             filter=partial(is_transfer_receiver, self.user_address)))

        if len(receive_assets) != 2:
            export_unknown(self.exporter, txinfo)
            return

        export_lp_withdraw_tx(
            self.exporter, txinfo,
            lp_asset, receive_assets[0], receive_assets[1],
            fee_amount, self.name)

    def _handle_tinymanv2_governance_create_lock(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        asset = get_transfer_asset(group[0])
        if asset.is_algo():
            fee_amount += asset.uint_amount
            asset = get_transfer_asset(group[1])

        export_stake_tx(self.exporter, txinfo, asset, fee_amount, self.name)

    def _handle_tinymanv2_governance_withdraw(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        asset = get_inner_transfer_asset(group[0])

        export_unstake_tx(self.exporter, txinfo, asset, fee_amount, self.name)

    def _handle_tinymanv2_governance_claim_rewards(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        asset = get_transfer_asset(group[0])
        if asset is not None and asset.is_algo():
            fee_amount += asset.uint_amount

        asset = get_inner_transfer_asset(group[-1])

        export_reward_tx(self.exporter, txinfo, asset, fee_amount, self.name)
