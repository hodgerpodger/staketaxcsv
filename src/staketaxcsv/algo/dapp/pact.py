from functools import partial

from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import (
    export_lp_deposit_tx,
    export_lp_stake_tx,
    export_lp_unstake_tx,
    export_lp_withdraw_tx,
    export_participation_rewards,
    export_reward_tx,
    export_swap_tx,
    export_unknown
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
    get_transfer_asset,
    is_app_call,
    is_app_optin,
    is_asset_optin,
    is_transaction_sender,
    is_transfer,
    is_transfer_receiver
)
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

APPLICATION_ID_PACT_ROUTER = 887109719

APPLICATION_ID_FOLKS_LENDING_POOL_ADAPTER = 1123472996

# TODO update names when app ABI is published
PACT_TRANSACTION_ROUTED_SWAP_1 = "hN2OEA=="         # ABI selector
PACT_TRANSACTION_ROUTED_SWAP_2 = "OowGzw=="         # ABI selector
PACT_TRANSACTION_LENDING_PRE_LP_ADD = "yGWKXA=="    # "pre_add_liquidity" ABI selector
PACT_TRANSACTION_LENDING_LP_ADD = "6tH4yQ=="        # "add_liquidity" ABI selector
PACT_TRANSACTION_LENDING_LP_REMOVE = "X9vVXQ=="     # "remove_liquidity" ABI selector
PACT_TRANSACTION_LENDING_POST_LP_REMOVE = "9DvuYQ=="    # "post_remove_liquidity" ABI selector
PACT_TRANSACTION_FARM_ESCROW_CREATE = "OIgacQ=="    # "create" ABI selector
PACT_TRANSACTION_FARM_UPDATE_STATE = "wxQK5w=="     # "update_state" ABI selector
PACT_TRANSACTION_FARM_UNSTAKE = "eIIs8A=="          # "unstake" ABI selector
PACT_TRANSACTION_FARM_CLAIM_REWARDS = "Sq6j8g=="    # "claim_rewards" ABI selector
PACT_TRANSACTION_INCREASE_QUOTA = "/95jeA=="        # "increase_opcode_quota" ABI selector

PACT_TRANSACTION_SWAP = "U1dBUA=="           # "SWAP"
PACT_TRANSACTION_LP_ADD = "QURETElR"         # "ADDLIQ"
PACT_TRANSACTION_LP_REMOVE = "UkVNTElR"      # "REMLIQ"

PACT_FARM_CONTRACTS = [
    1078150993,  # ALGO/GALGO
    1078150949,  # ALGO/USDC
    1124036810,  # FALGO/FGALGO
    1078152165,  # ALGO/GOBTC
    1078151177,  # ALGO/DEFLY
    1078151255,  # ALGO/GOETH
    1124031333,  # FALGO/FUSDC
    1083532607,  # GOLD$/GOUSD
    1124035184,  # FUSDC/FUSDT
    1124038236,  # FALGO/FWETH
    1078152671,  # ALGO/GARD
    1083532545,  # SILVER$/GOUSD
    1078152494,  # ALGO/FINITE
    1078152761,  # ALGO/VEST
    1124037645,  # FALGO/FWBTC
    1078151670,  # ALGO/OPUL
    1140566471,  # ALGO/ASASTATS
    1139918641,  # ALGO/COOP
    1078153222,  # USDC/FINITE
    1139918356,  # ALGO/GOLD$
    1078153857,  # GOBTC/FINITE
    1124040011,  # FALGO/FGARD
    1088353673,  # GOMINT/GOUSD
    1078153307,  # USDC/VOTE
    1088354046,  # ALGO/COSG
    1092375502,  # GOUSD/GALGO
    1078151580,  # ALGO/VOTE
    1078152384,  # ALGO/GOMINT
    1088353898,  # ALGO/XET
    1078153752,  # GOBTC/VOTE
    1100675834,  # GOETH/PEPE
    1088353843,  # USDC/OPUL
    1078153599,  # USDT/USDC
    1078152948,  # USDC/XUSD
    1088353985,  # USDC/VYBE
    1088353738,  # VOTE/GALGO
    1139918886,  # ALGO/DHARM
    1101161755,  # GOUSD/PEPE
    1139918482,  # ALGO/VYBE
    1083532721,  # GOUSD/XUSD
    1038501616,  # ALGO/GOETH
    1038503241,  # ALGO/GOMINT
    1078153044,  # USDC/GOUSD
    1150765030,  # USDC/GOUSD
    1078154025,  # GOETH/WETH
    1150764423,  # GOETH/WETH
    1078153466,  # GOBTC/WBTC
    1150764376,  # GOBTC/WBTC
    1248669934,  # FUSDC/FEURS
    1248669985,  # FUSDC/FEURS
    1124037645,  # FALGO/FwBTC
    1124038236,  # FALGO/FwETH
    1170254199,  # FALGO/FAVAX
    1177033931,  # FALGO/FSOL
    1150765092,  # GOLD$/XUSD
    1150765145,  # SILVER$/XUSD
]


class Pact(Dapp):
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "Pact"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return (self._is_pact_routed_swap(group)
                    or self._is_pact_swap(group)
                    or self._is_pact_lp_add(group)
                    or self._is_pact_lp_remove(group)
                    or self._is_pact_lending_lp_add(group)
                    or self._is_pact_lending_lp_remove(group)
                    or self._is_pact_farm_escrow_create(group)
                    or self._is_pact_farm_stake(group)
                    or self._is_pact_farm_unstake(group)
                    or self._is_pact_farm_claim_rewards(group)
                    or self._is_pact_farm_unstake_and_claim_rewards(group))

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        reward = Algo(group[0]["sender-rewards"])
        export_participation_rewards(reward, self.exporter, txinfo)

        txinfo.comment = self.name
        if self._is_pact_routed_swap(group):
            self._handle_pact_routed_swap(group, txinfo)

        elif self._is_pact_swap(group):
            handle_swap(self.user_address, group, self.exporter, txinfo)

        elif self._is_pact_lp_add(group):
            handle_lp_add(group, self.exporter, txinfo)

        elif self._is_pact_lp_remove(group):
            handle_lp_remove(group, self.exporter, txinfo)

        elif self._is_pact_lending_lp_add(group):
            self._handle_pact_lending_lp_add(group, txinfo)

        elif self._is_pact_lending_lp_remove(group):
            self._handle_pact_lending_lp_remove(group, txinfo)

        elif self._is_pact_farm_escrow_create(group):
            pass

        elif self._is_pact_farm_stake(group):
            self._handle_pact_farm_stake(group, txinfo)

        elif self._is_pact_farm_unstake(group):
            self._handle_pact_farm_unstake(group, txinfo)

        elif self._is_pact_farm_claim_rewards(group):
            self._handle_pact_farm_claim_rewards(group, txinfo)

        elif self._is_pact_farm_unstake_and_claim_rewards(group):
            self._handle_pact_farm_unstake(group, txinfo)

        else:
            export_unknown(self.exporter, txinfo)

    def _is_pact_swap(self, group):
        if not is_swap_group(self.user_address, group):
            return False

        return is_app_call(group[-1], app_args=PACT_TRANSACTION_SWAP)

    def _is_pact_routed_swap(self, group):
        if len(group) < 2:
            return False

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        transaction = group[i]
        if not is_transfer(transaction):
            return False

        if not is_transaction_sender(self.user_address, transaction):
            return False

        if is_asset_optin(transaction):
            return False

        return is_app_call(group[-1],
                           APPLICATION_ID_PACT_ROUTER,
                           [PACT_TRANSACTION_ROUTED_SWAP_1, PACT_TRANSACTION_ROUTED_SWAP_2])

    def _is_pact_lp_add(self, group):
        if not is_lp_add_group(self.user_address, group):
            return False

        return is_app_call(group[-1], app_args=PACT_TRANSACTION_LP_ADD)

    def _is_pact_lp_remove(self, group):
        if not is_lp_remove_group(self.user_address, group):
            return False

        return is_app_call(group[-1], app_args=PACT_TRANSACTION_LP_REMOVE)

    def _is_pact_lending_lp_add(self, group):
        length = len(group)
        if length < 4 or length > 5:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_FOLKS_LENDING_POOL_ADAPTER, PACT_TRANSACTION_LENDING_LP_ADD):
            return False

        if not is_app_call(group[-2], APPLICATION_ID_FOLKS_LENDING_POOL_ADAPTER, PACT_TRANSACTION_LENDING_PRE_LP_ADD):
            return False

        if not is_transfer(group[-3]):
            return False

        if not is_transaction_sender(self.user_address, group[-3]):
            return False

        if not is_transfer(group[-4]):
            return False

        return is_transaction_sender(self.user_address, group[-4])

    def _is_pact_lending_lp_remove(self, group):
        length = len(group)
        if length < 3 or length > 5:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_FOLKS_LENDING_POOL_ADAPTER, PACT_TRANSACTION_LENDING_POST_LP_REMOVE):
            return False

        if not is_app_call(group[-2], APPLICATION_ID_FOLKS_LENDING_POOL_ADAPTER, PACT_TRANSACTION_LENDING_LP_REMOVE):
            return False

        if not is_transaction_sender(self.user_address, group[-3]):
            return False

        return is_transaction_sender(self.user_address, group[-3])

    def _is_pact_farm_escrow_create(self, group):
        if len(group) != 3:
            return False

        if not is_app_optin(group[-1]):
            return False

        if not is_app_call(group[-2], app_args=PACT_TRANSACTION_FARM_ESCROW_CREATE):
            return False

        if not is_transfer(group[-3]):
            return False

        return is_transaction_sender(self.user_address, group[-3])

    def _is_pact_farm_stake(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        if not is_app_call(group[-1], PACT_FARM_CONTRACTS, PACT_TRANSACTION_FARM_UPDATE_STATE):
            return False

        if not is_transfer(group[0]):
            return False

        return is_transaction_sender(self.user_address, group[0])

    def _is_pact_farm_unstake(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        if not is_app_call(group[0], app_args=PACT_TRANSACTION_FARM_UNSTAKE):
            return False

        return is_app_call(group[1], PACT_FARM_CONTRACTS, PACT_TRANSACTION_FARM_UPDATE_STATE)

    def _is_pact_farm_claim_rewards(self, group):
        if len(group) != 2:
            return False

        if not is_app_call(group[-1], PACT_FARM_CONTRACTS, PACT_TRANSACTION_FARM_CLAIM_REWARDS):
            return False

        return is_app_call(group[-2], PACT_FARM_CONTRACTS, PACT_TRANSACTION_FARM_UPDATE_STATE)

    def _is_pact_farm_unstake_and_claim_rewards(self, group):
        if len(group) != 4:
            return False

        if not is_app_call(group[0], app_args=PACT_TRANSACTION_INCREASE_QUOTA):
            return False

        if not is_app_call(group[1], app_args=PACT_TRANSACTION_FARM_UNSTAKE):
            return False

        if not is_app_call(group[2], PACT_FARM_CONTRACTS, PACT_TRANSACTION_FARM_UPDATE_STATE):
            return False

        return is_app_call(group[3], PACT_FARM_CONTRACTS, PACT_TRANSACTION_FARM_CLAIM_REWARDS)

    def _handle_pact_routed_swap(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        length = len(group)
        i = 0
        while i < length and is_asset_optin(group[i]):
            i += 1

        send_asset = None
        receive_asset = None
        for transaction in group[i:]:
            if is_transfer(transaction):
                asset = get_transfer_asset(transaction)
                send_asset = asset if send_asset is None else send_asset + asset
            elif is_app_call(transaction, app_args=[PACT_TRANSACTION_SWAP,
                                                    PACT_TRANSACTION_ROUTED_SWAP_1,
                                                    PACT_TRANSACTION_ROUTED_SWAP_2]):
                asset = get_inner_transfer_asset(transaction,
                                                 filter=partial(is_transfer_receiver, self.user_address))
                if asset is not None:
                    receive_asset = asset if receive_asset is None else receive_asset + asset

        if send_asset is not None and receive_asset is not None:
            export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Router")
        else:
            export_unknown(self.exporter, txinfo)

    def _handle_pact_lending_lp_add(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        lp_asset = get_inner_transfer_asset(group[-1],
                                            filter=partial(is_transfer_receiver, self.user_address))

        send_asset_1 = get_transfer_asset(group[-4])
        send_asset_2 = get_transfer_asset(group[-3])

        export_lp_deposit_tx(self.exporter, txinfo, send_asset_1, send_asset_2, lp_asset, fee_amount, self.name)

    def _handle_pact_lending_lp_remove(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        lp_asset = get_transfer_asset(group[-3])

        receive_assets = list(generate_inner_transfer_assets(group[-1],
                                                             filter=partial(is_transfer_receiver, self.user_address)))

        if len(receive_assets) != 2:
            export_unknown(self.exporter, txinfo)
            return

        export_lp_withdraw_tx(
            self.exporter, txinfo,
            lp_asset, receive_assets[0], receive_assets[1],
            fee_amount, self.name)

    def _handle_pact_farm_stake(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        lp_asset = get_transfer_asset(group[0])

        export_lp_stake_tx(self.exporter, txinfo, lp_asset, fee_amount, self.name)

    def _handle_pact_farm_unstake(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        lp_asset = get_inner_transfer_asset(group[0],
                                            filter=partial(is_transfer_receiver, self.user_address))
        if lp_asset is None:
            lp_asset = get_inner_transfer_asset(group[1],
                                                filter=partial(is_transfer_receiver, self.user_address))

        export_lp_unstake_tx(self.exporter, txinfo, lp_asset, 0, self.name, 0)

        reward_assets = list(generate_inner_transfer_assets(group[-1],
                                                            filter=partial(is_transfer_receiver, self.user_address)))
        reward_fee = fee_amount / len(reward_assets)
        for asset in reward_assets:
            export_reward_tx(self.exporter, txinfo, asset, reward_fee, self.name)

    def _handle_pact_farm_claim_rewards(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[-1])

        export_reward_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name)
