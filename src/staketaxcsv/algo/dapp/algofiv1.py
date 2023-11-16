import base64
from decimal import Decimal

from algosdk import encoding
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.cost_basis import DepositCostBasisTracker
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import (
    export_borrow_tx,
    export_deposit_collateral_tx,
    export_liquidate_tx,
    export_lp_deposit_tx,
    export_lp_stake_tx,
    export_lp_unstake_tx,
    export_lp_withdraw_tx,
    export_participation_rewards,
    export_repay_tx,
    export_reward_tx,
    export_swap_tx,
    export_unknown,
    export_withdraw_collateral_tx,
)
from staketaxcsv.algo.handle_transfer import handle_governance_reward_transaction, is_governance_reward_transaction
from staketaxcsv.algo.transaction import (
    get_app_global_state_delta_value,
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_app_call,
    is_app_clear,
    is_app_optin,
    is_asa_transfer,
    is_asset_optin,
    is_transaction_sender,
    is_transfer
)

from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo


# For reference
# https://github.com/Algofiorg/algofi-amm-py-sdk
# https://github.com/Algofiorg/algofi-amm-js-sdk
# https://github.com/Algofiorg/algofi-py-sdk
# https://github.com/Algofiorg/algofi-lend-js-sdk

APPLICATION_ID_ALGOFI_AMM_MANAGER = 605753404
APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER = 658336870
APPLICATION_ID_ALGOFI_LENDING_MANAGER = 465818260
APPLICATION_ID_ALGOFI_STABILITY_MANAGER = 705663269
APPLICATION_ID_ALGOFI_VALGO_MARKET = 465814318


APPLICATION_ID_ALGOFI_MANAGERS = [
    APPLICATION_ID_ALGOFI_AMM_MANAGER,
    APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER,
    APPLICATION_ID_ALGOFI_LENDING_MANAGER,
    APPLICATION_ID_ALGOFI_STABILITY_MANAGER
]

# fetch market variables
# update prices
# update protocol data
# dummy transactions
ALGOFI_NUM_INIT_TXNS = 12

ALGOFI_TRANSACTION_SWAP_EXACT_FOR = "c2Vm"          # "sef"
ALGOFI_TRANSACTION_SWAP_FOR_EXACT = "c2Zl"          # "sfe"
ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL = "cnNy"    # "rsr"

ALGOFI_TRANSACTION_CLAIM_REWARDS = "Y3I="           # "cr"

ALGOFI_TRANSACTION_POOL = "cA=="                    # "p"
ALGOFI_TRANSACTION_REDEEM_POOL_ASSET1_RESIDUAL = "cnBhMXI="   # "rpa1r"
ALGOFI_TRANSACTION_REDEEM_POOL_ASSET2_RESIDUAL = "cnBhMnI="   # "rpa2r"
ALGOFI_TRANSACTION_BURN_ASSET1_OUT = "YmExbw=="     # "ba1o"
ALGOFI_TRANSACTION_BURN_ASSET2_OUT = "YmEybw=="     # "ba2o"


ALGOFI_TRANSACTION_MINT_TO_COLLATERAL = "bXQ="      # "mt"
ALGOFI_TRANSACTION_REMOVE_COLLATERAL_UNDERLYING = "cmN1"      # "rcu"
ALGOFI_TRANSACTION_BORROW = "Yg=="                  # "b"
ALGOFI_TRANSACTION_REPAY_BORROW = "cmI="            # "rb"
ALGOFI_TRANSACTION_LIQUIDATE = "bA=="               # "l"

ALGOFI_TRANSACTION_FLASH_LOAN = "Zmw="              # "fl"

ALGOFI_TRANSACTION_OPT_OUT = "b28="                 # "oo"

ALGOFI_TRANSACTION_SYNC_VAULT = "c3Y="              # "sv"

ALGOFI_MANAGER_USER_STORAGE_ACCOUNT = "dXNh"        # "usa"

UNDERLYING_ASSETS = {
    # bALGO -> ALGO
    465818547: 0,
    # bUSDC -> USDC
    465818553: 31566704,
    # bgoBTC -> goBTC
    465818554: 386192725,
    # bgoETH -> goETH
    465818555: 386195940,
    # bSTBL -> STBL
    465818563: 465865291,
}

BANK_ASSETS = {v: k for k, v in UNDERLYING_ASSETS.items()}

ALGOFI_MARKET_CONTRACTS = [
    465814065,  # ALGO
    465814103,  # USDC
    465814149,  # goBTC
    465814222,  # goETH
    465814278,  # STBL
    465814318,  # vALGO
]

ALGOFI_STAKING_CONTRACTS = {
    # Manager App ID
    482625868: "STBL",
    553869413: "Tinyman STBL-USDC",
    611804624: "STBL-ALGO",
    611869320: "STBL-USDC",
    635813909: "STBL-XET",
    635863793: "STBL-GOBTC",
    635866213: "STBL-GOETH",
    674527132: "OPUL",
    637795072: "STBL-OPUL",
    641500474: "DEFLY",
    639747739: "STBL-DEFLY",
    647785804: "STBL-ZONE",
    661193019: "STBL-USDC",  # NanoSwap
    661204747: "STBL-USDT",  # NanoSwap
    661247364: "USDC-USDT",  # NanoSwap
    705663269: "STBL-USDC",  # NanoSwap Stability
    764407972: "STBL-goMINT",
    # Market App ID
    482608867: "STBL",
    553866305: "Tinyman STBL-USDC",
    611801333: "STBL-ALGO",
    611867642: "STBL-USDC",
    635812850: "STBL-XET",
    635860537: "STBL-GOBTC",
    635864509: "STBL-GOETH",
    674526408: "OPUL",
    637793356: "STBL-OPUL",
    641499935: "DEFLY",
    639747119: "STBL-DEFLY",
    647785158: "STBL-ZONE",
    661192413: "STBL-USDC",  # NanoSwap
    661199805: "STBL-USDT",  # NanoSwap
    661207804: "USDC-USDT",  # NanoSwap
    705657303: "STBL-USDC",  # NanoSwap Stability
    764406975: "STBL-goMINT",
}

ALGOFI_STATE_KEY_BANK_TO_UNDERLYING_EXCHANGE = "YnQ="  # "bt"


class AlgofiV1(Dapp):
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter
        self.storage_address = self._get_algofi_storage_address(account)
        self.cost_basis_tracker = DepositCostBasisTracker()

    @property
    def name(self):
        return "AlgoFi v1"

    def get_extra_transactions(self) -> list:
        txs = []
        if self.storage_address is None:
            return txs

        storage_txs = self.indexer.get_all_transactions(self.storage_address)
        txs.extend(self._get_algofi_liquidate_transactions(storage_txs))
        txs.extend(self._get_algofi_governance_rewards_transactions(storage_txs))
        return txs

    def is_dapp_transaction(self, group: list) -> bool:
        return (self._is_algofi_zap(group)
                    or self._is_algofi_swap(group)
                    or self._is_algofi_claim_rewards(group)
                    or self._is_algofi_lp_add(group)
                    or self._is_algofi_lp_remove(group)
                    or self._is_algofi_borrow(group)
                    or self._is_algofi_repay_borrow(group)
                    or self._is_algofi_deposit_collateral(group)
                    or self._is_algofi_remove_collateral(group)
                    or self._is_algofi_liquidate(group)
                    or self._is_algofi_flash_loan(group)
                    or is_governance_reward_transaction(self.storage_address, group)
                    or self._is_algofi_sync_vault(group)
                    or self._is_algofi_manager_optin(group)
                    or self._is_algofi_manager_optout(group))

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        reward = Algo(group[0]["sender-rewards"])
        export_participation_rewards(reward, self.exporter, txinfo)

        if self._is_algofi_zap(group):
            self._handle_algofi_zap(group, txinfo)

        elif self._is_algofi_swap(group):
            self._handle_algofi_swap(group, txinfo)

        elif self._is_algofi_claim_rewards(group):
            self._handle_algofi_claim_rewards(group, txinfo)

        elif self._is_algofi_lp_add(group):
            self._handle_algofi_lp_add(group, txinfo)

        elif self._is_algofi_lp_remove(group):
            self._handle_algofi_lp_remove(group, txinfo)

        elif self._is_algofi_borrow(group):
            self._handle_algofi_borrow(group, txinfo)

        elif self._is_algofi_repay_borrow(group):
            self._handle_algofi_repay_borrow(group, txinfo)

        elif self._is_algofi_deposit_collateral(group):
            self._handle_algofi_deposit_collateral(group, txinfo)

        elif self._is_algofi_remove_collateral(group):
            self._handle_algofi_withdraw_collateral(group, txinfo)

        elif self._is_algofi_liquidate(group):
            self._handle_algofi_liquidate(group, txinfo)

        elif self._is_algofi_flash_loan(group):
            self._handle_algofi_flash_loan(group, txinfo)

        elif is_governance_reward_transaction(self.storage_address, group):
            handle_governance_reward_transaction(group, self.exporter, txinfo)

        elif self._is_algofi_sync_vault(group):
            pass

        elif self._is_algofi_manager_optin(group):
            pass

        elif self._is_algofi_manager_optout(group):
            pass

        else:
            export_unknown(self.exporter, txinfo)

    def _get_algofi_storage_address(self, account):
        if account is None:
            return None

        local_state = next((app for app in account.get("apps-local-state", [])
                            if app["id"] == APPLICATION_ID_ALGOFI_LENDING_MANAGER), None)
        if local_state is None:
            return None

        if local_state.get("deleted"):
            transactions = self.indexer.get_transactions_by_app(APPLICATION_ID_ALGOFI_LENDING_MANAGER,
                                                                local_state.get("opted-in-at-round"),
                                                                self.user_address)
            if not transactions:
                return None

            tx = transactions[0]
            if not is_app_optin(tx):
                return None

            for state in tx.get("local-state-delta", []):
                for delta in state.get("delta", []):
                    if delta["key"] == ALGOFI_MANAGER_USER_STORAGE_ACCOUNT:
                        raw_address = delta["value"]["bytes"]
                        return encoding.encode_address(base64.b64decode(raw_address.strip()))
        else:
            for keyvalue in local_state.get("key-value", []):
                if keyvalue["key"] == ALGOFI_MANAGER_USER_STORAGE_ACCOUNT:
                    raw_address = keyvalue["value"]["bytes"]
                    return encoding.encode_address(base64.b64decode(raw_address.strip()))

        return None

    def _get_algofi_liquidate_transactions(self, transactions):
        return [tx for tx in transactions if is_app_call(tx, app_args=ALGOFI_TRANSACTION_LIQUIDATE)]

    def _get_algofi_governance_rewards_transactions(self, transactions):
        return [tx for tx in transactions if is_governance_reward_transaction(self.storage_address, [tx])]

    def _is_algofi_zap(self, group):
        length = len(group)
        if length < 7 or length > 9:
            return False

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        return self._is_algofi_swap(group[:i + 2]) and self._is_algofi_lp_add(group[i + 2:])

    def _is_algofi_swap_exact_for(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        if not is_transfer(group[i]):
            return False

        i += 1
        if i == length:
            return False

        return is_app_call(group[-1],
                        app_args=ALGOFI_TRANSACTION_SWAP_EXACT_FOR,
                        foreign_app=[APPLICATION_ID_ALGOFI_AMM_MANAGER, APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER])

    def _is_algofi_swap_for_exact(self, group):
        length = len(group)
        if length < 3 or length > 4:
            return False

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        if not is_transfer(group[i]):
            return False

        i += 1
        if i == length:
            return False

        if not is_app_call(group[i],
                        app_args=ALGOFI_TRANSACTION_SWAP_FOR_EXACT,
                        foreign_app=[APPLICATION_ID_ALGOFI_AMM_MANAGER, APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER]):
            return False

        return is_app_call(group[-1], app_args=ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL)

    def _is_algofi_swap(self, group):
        return self._is_algofi_swap_exact_for(group) or self._is_algofi_swap_for_exact(group)

    def _is_algofi_claim_rewards(self, group):
        if len(group) != ALGOFI_NUM_INIT_TXNS + 1:
            return False

        app_ids = [APPLICATION_ID_ALGOFI_LENDING_MANAGER, APPLICATION_ID_ALGOFI_STABILITY_MANAGER]
        app_ids.extend(list(ALGOFI_STAKING_CONTRACTS.keys()))
        return is_app_call(group[-1], app_ids, ALGOFI_TRANSACTION_CLAIM_REWARDS)

    def _is_algofi_lp_add(self, group):
        length = len(group)
        # Optional ASA opt-in
        if length != 5 and length != 6:
            return False

        if not is_app_call(group[-1], app_args=ALGOFI_TRANSACTION_REDEEM_POOL_ASSET2_RESIDUAL):
            return False

        if not is_app_call(group[-2], app_args=ALGOFI_TRANSACTION_REDEEM_POOL_ASSET1_RESIDUAL):
            return False

        return is_app_call(group[-3], app_args=ALGOFI_TRANSACTION_POOL)

    def _is_algofi_lp_remove(self, group):
        if len(group) != 3:
            return False

        if not is_asa_transfer(group[0]):
            return False

        if not is_app_call(group[1], app_args=ALGOFI_TRANSACTION_BURN_ASSET1_OUT):
            return False

        return is_app_call(group[2], app_args=ALGOFI_TRANSACTION_BURN_ASSET2_OUT)

    def _is_algofi_borrow(self, group):
        if len(group) != ALGOFI_NUM_INIT_TXNS + 2:
            return False

        if not is_app_call(group[-1],
                           app_args=ALGOFI_TRANSACTION_BORROW,
                           foreign_app=APPLICATION_ID_ALGOFI_LENDING_MANAGER):
            return False

        return is_app_call(group[-2], APPLICATION_ID_ALGOFI_LENDING_MANAGER, ALGOFI_TRANSACTION_BORROW)

    def _is_algofi_repay_borrow(self, group):
        if len(group) != ALGOFI_NUM_INIT_TXNS + 3:
            return False

        if not is_app_call(group[-2],
                           app_args=ALGOFI_TRANSACTION_REPAY_BORROW,
                           foreign_app=APPLICATION_ID_ALGOFI_LENDING_MANAGER):
            return False

        return is_app_call(group[-3], APPLICATION_ID_ALGOFI_LENDING_MANAGER, ALGOFI_TRANSACTION_REPAY_BORROW)

    def _is_algofi_deposit_collateral(self, group):
        if len(group) != ALGOFI_NUM_INIT_TXNS + 3:
            return False

        app_ids = list(ALGOFI_STAKING_CONTRACTS.keys())
        app_ids.extend(ALGOFI_MARKET_CONTRACTS)
        return is_app_call(group[-2], app_ids, ALGOFI_TRANSACTION_MINT_TO_COLLATERAL)

    def _is_algofi_remove_collateral(self, group):
        if len(group) != ALGOFI_NUM_INIT_TXNS + 2:
            return False

        app_ids = list(ALGOFI_STAKING_CONTRACTS.keys())
        app_ids.extend(ALGOFI_MARKET_CONTRACTS)
        return is_app_call(group[-1], app_ids, ALGOFI_TRANSACTION_REMOVE_COLLATERAL_UNDERLYING)

    def _is_algofi_liquidate(self, group):
        length = len(group)
        # Liquidatee group transactions are trimmed down
        if length != 2 and length != ALGOFI_NUM_INIT_TXNS + 4:
            return False

        return is_app_call(group[-1],
                           app_args=ALGOFI_TRANSACTION_LIQUIDATE,
                           foreign_app=APPLICATION_ID_ALGOFI_LENDING_MANAGER)

    def _is_algofi_flash_loan(self, group):
        # Borrow + tx group + repay
        if len(group) < 3:
            return False

        return is_app_call(group[0],
                           app_args=ALGOFI_TRANSACTION_FLASH_LOAN,
                           foreign_app=[APPLICATION_ID_ALGOFI_AMM_MANAGER, APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER])

    def _is_algofi_sync_vault(self, group):
        if len(group) != ALGOFI_NUM_INIT_TXNS + 2:
            return False

        return is_app_call(group[-1],
                           app_args=ALGOFI_TRANSACTION_SYNC_VAULT,
                           foreign_app=APPLICATION_ID_ALGOFI_LENDING_MANAGER)

    def _is_algofi_manager_optin(self, group):
        if len(group) != 2:
            return False

        if not is_transfer(group[0]):
            return False

        if is_asset_optin(group[0]):
            return False

        contracts = APPLICATION_ID_ALGOFI_MANAGERS
        contracts.extend(ALGOFI_STAKING_CONTRACTS)
        if not is_app_call(group[1], contracts):
            return False

        return is_app_optin(group[1])

    def _is_algofi_manager_optout(self, group):
        if len(group) != 2:
            return False

        if not is_app_call(group[0], app_args=ALGOFI_TRANSACTION_OPT_OUT, foreign_app=APPLICATION_ID_ALGOFI_MANAGERS):
            return False

        if not is_app_call(group[1], APPLICATION_ID_ALGOFI_MANAGERS):
            return False

        return is_app_clear(group[1])

    def _handle_algofi_zap(self, group, txinfo):
        i = 0
        if is_asset_optin(group[i]):
            i += 1

        self._handle_algofi_swap(group[:i + 2], txinfo, 0)
        self._handle_algofi_lp_add(group[i + 2:], txinfo, 1)

    def _handle_algofi_swap(self, group, txinfo, z_index=0):
        fee_amount = get_fee_amount(self.user_address, group)

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        send_asset = get_transfer_asset(group[i])
        receive_asset = get_inner_transfer_asset(group[i + 1])

        if is_app_call(group[-1], app_args=ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL):
            redeem_asset = get_inner_transfer_asset(group[-1])
            if redeem_asset is not None:
                send_asset -= redeem_asset

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name, z_index)

    def _handle_algofi_lp_add(self, group, txinfo, z_index=0):
        fee_amount = get_fee_amount(self.user_address, group)

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        send_asset_1 = get_transfer_asset(group[i])

        i += 1
        send_asset_2 = get_transfer_asset(group[i])

        i += 1
        lp_asset = get_inner_transfer_asset(group[i])

        i += 1
        redeem_asset_1 = get_inner_transfer_asset(group[i])
        if redeem_asset_1 is not None:
            send_asset_1 -= redeem_asset_1

        i += 1
        redeem_asset_2 = get_inner_transfer_asset(group[i])
        if redeem_asset_2 is not None:
            send_asset_2 -= redeem_asset_2

        export_lp_deposit_tx(
            self.exporter, txinfo, send_asset_1, send_asset_2, lp_asset, fee_amount, self.name, z_index)

    def _handle_algofi_lp_remove(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        lp_asset = get_transfer_asset(group[0])

        receive_asset_1 = get_inner_transfer_asset(group[1])

        receive_asset_2 = get_inner_transfer_asset(group[2])

        export_lp_withdraw_tx(
            self.exporter, txinfo, lp_asset, receive_asset_1, receive_asset_2, fee_amount, self.name)

    def _handle_algofi_claim_rewards(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        app_transaction = group[-1]
        inner_transactions = app_transaction.get("inner-txns", [])

        length = len(inner_transactions)
        for transaction in inner_transactions:
            reward = get_transfer_asset(transaction)
            export_reward_tx(self.exporter, txinfo, reward, fee_amount / length, self.name)

    def _handle_algofi_borrow(self, group, txinfo, z_index=0):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[-1])

        export_borrow_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name + " Borrow", z_index)

    def _handle_algofi_repay_borrow(self, group, txinfo, z_index=0):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[-1])

        if is_app_call(group[-2], app_args=ALGOFI_TRANSACTION_REPAY_BORROW):
            residual_asset = get_inner_transfer_asset(group[-2])
            if residual_asset is not None:
                send_asset -= residual_asset

        export_repay_tx(self.exporter, txinfo, send_asset, fee_amount, self.name + " Repay", z_index)

    def _handle_algofi_liquidate(self, group, txinfo):
        app_transaction = group[-1]
        if is_transaction_sender(self.user_address, app_transaction):
            fee_amount = get_fee_amount(self.user_address, group)

            send_asset = get_transfer_asset(group[-2])

            receive_asset = get_inner_transfer_asset(app_transaction, UNDERLYING_ASSETS)
            export_liquidate_tx(
                self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " liquidation")
        else:
            repay_asset = get_inner_transfer_asset(app_transaction, UNDERLYING_ASSETS)
            export_repay_tx(self.exporter, txinfo, repay_asset, 0, self.name + " liquidation")

    def _handle_algofi_flash_loan(self, group, txinfo):
        self._handle_algofi_borrow(group[:1], txinfo, 0)
        self._handle_algofi_swap(group[1:-1], txinfo, 1)
        self._handle_algofi_repay_borrow(group[-1:], txinfo, 2)

    def _handle_algofi_deposit_collateral(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[-1])

        app_transaction = group[-2]
        app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
        if app_id in ALGOFI_STAKING_CONTRACTS:
            export_lp_stake_tx(
                self.exporter, txinfo, send_asset, fee_amount,
                self.name + " " + ALGOFI_STAKING_CONTRACTS[app_id] + " staking")
            return

        is_vault = (app_id == APPLICATION_ID_ALGOFI_VALGO_MARKET)
        comment = self.name + (" Vault" if is_vault else "")
        export_deposit_collateral_tx(self.exporter, txinfo, send_asset, fee_amount, comment)

        if is_vault:
            return

        value = get_app_global_state_delta_value(app_transaction, ALGOFI_STATE_KEY_BANK_TO_UNDERLYING_EXCHANGE)
        if value is None:
            return

        exchange_rate = Decimal(value["uint"]) / Decimal(10 ** 9)
        basset_amount = int(send_asset.uint_amount / exchange_rate)
        basset = Asset(BANK_ASSETS[send_asset.id], basset_amount)
        self.cost_basis_tracker.deposit(send_asset, basset)

    def _handle_algofi_withdraw_collateral(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        app_transaction = group[-1]
        receive_asset = get_inner_transfer_asset(app_transaction)

        app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
        if app_id in ALGOFI_STAKING_CONTRACTS:
            export_lp_unstake_tx(
                self.exporter, txinfo, receive_asset, fee_amount,
                self.name + " " + ALGOFI_STAKING_CONTRACTS[app_id] + " unstaking")
            return

        is_vault = (app_id == APPLICATION_ID_ALGOFI_VALGO_MARKET)
        comment = self.name + (" Vault" if is_vault else "")
        export_withdraw_collateral_tx(self.exporter, txinfo, receive_asset, fee_amount, comment, 0)

        if is_vault:
            return

        value = get_app_global_state_delta_value(app_transaction, ALGOFI_STATE_KEY_BANK_TO_UNDERLYING_EXCHANGE)
        if value is None:
            return

        exchange_rate = Decimal(value["uint"]) / Decimal(10 ** 9)
        basset_amount = int(receive_asset.uint_amount / exchange_rate)
        basset = Asset(BANK_ASSETS[receive_asset.id], basset_amount)
        interest = self.cost_basis_tracker.withdraw(basset, receive_asset)
        export_reward_tx(self.exporter, txinfo, interest, fee_amount, self.name + " Interest", 1)
