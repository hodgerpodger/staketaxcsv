from functools import partial
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import (
    export_borrow_tx,
    export_deposit_collateral_tx,
    export_repay_tx,
    export_spend_fee_tx,
    export_swap_tx,
    export_unknown,
    export_withdraw_collateral_tx,
)
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transaction_note,
    get_transfer_asset,
    is_app_call,
    is_asset_optin,
    is_transaction_sender,
    is_transfer,
    is_transfer_receiver
)

# For reference
# https://github.com/Folks-Finance/folks-finance-js-sdk
# https://docs.folks.finance/developer/contracts

COMMENT_FOLKSV2 = "Folks Finance"

APPLICATION_ID_FOLKSV2_POOL_MANAGER = 971350278
APPLICATION_ID_FOLKSV2_DEPOSIT = 971353536
APPLICATION_ID_FOLKSV2_LOANS = [
    971388781,  # General
    971388977,  # Stablecoin Efficiency
    971389489,  # ALGO Efficiency
]
APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER = 971333964
APPLICATION_ID_FOLKSV2_OP_UP = 971335937  # Oracle Price Update?

APPLICATION_ID_FOLKSV2_POOLS = [
    971368268,   # ALGO
    971370097,   # gALGO
    971372237,   # USDC
    971372700,   # USDt
    971373361,   # goBTC
    971373611,   # goETH
    1044267181,  # OPUL
]

NOTE_FOLKSV2_DEPOSIT_APP = "da"
NOTE_FOLKSV2_LOAN_APP = "la"
NOTE_FOLKSV2_LOAN_NAME = "ff-name"

FOLKSV2_TRANSACTION_DEPOSIT_ESCROW_OPTIN = "sx8Gbg=="       # "opt_escrow_into_asset" ABI selector
FOLKSV2_TRANSACTION_DEPOSIT = "udVC+w=="                    # "deposit" ABI selector
FOLKSV2_TRANSACTION_DEPOSIT_WITHDRAW = "ruOUyw=="           # "withdraw" ABI selector
FOLKSV2_TRANSACTION_LOAN_ADD_COLLATERAL = "aV6pHw=="        # "add_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_SYNC_COLLATERAL = "YLBwBQ=="       # "sync_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_BORROW = "l9QG5g=="                # "borrow" ABI selector
FOLKSV2_TRANSACTION_LOAN_REPAY_WITH_TXN = "o8ijmA=="        # "repay_with_txn" ABI selector
FOLKSV2_TRANSACTION_LOAN_REDUCE_COLLATERAL = "kXRHtw=="     # "reduce_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_REMOVE_COLLATERAL = "Iq24qQ=="     # "remove_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_REMOVE_LOAN = "UL3+hg=="           # "remove_loan" ABI selector
FOLKSV2_TRANSACTION_LOAN_SWAP_BEGIN = "GIPo0w=="            # "swap_collateral_begin" ABI selector
FOLKSV2_TRANSACTION_LOAN_SWAP_END = "SBn0/w=="              # "swap_collateral_end" ABI selector

APPLICATION_ID_DEFLEX_ORDER_ROUTER = 989365103
DEFLEX_TRANSACTION_SWAP_FINALIZE = "tTD7Hw=="  # "User_swap_finalize" ABI selector


def _is_folksv2_deposit(wallet_address, group):
    length = len(group)
    if length < 2 or length > 5:
        return False

    if not is_app_call(group[-1], APPLICATION_ID_FOLKSV2_POOLS, FOLKSV2_TRANSACTION_DEPOSIT):
        return False

    if not is_transfer(group[-2]):
        return False

    return is_transaction_sender(wallet_address, group[-2])


def _is_folksv2_withdraw(group):
    length = len(group)
    if length > 2:
        return False

    if length == 2 and not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
        return False

    return is_app_call(group[-1], APPLICATION_ID_FOLKSV2_DEPOSIT, FOLKSV2_TRANSACTION_DEPOSIT_WITHDRAW)


def _is_folksv2_create_loan(wallet_address, group):
    if len(group) != 2:
        return False

    if not is_transfer(group[0]):
        return False

    if not is_transaction_sender(wallet_address, group[0]):
        return False

    note = get_transaction_note(group[0], len(NOTE_FOLKSV2_LOAN_NAME))
    if note != NOTE_FOLKSV2_LOAN_NAME:
        return False

    if not is_transfer(group[1]):
        return False

    if not is_transaction_sender(wallet_address, group[1]):
        return False

    note = get_transaction_note(group[1], len(NOTE_FOLKSV2_LOAN_APP))
    return note == NOTE_FOLKSV2_LOAN_APP


def _is_folksv2_move_to_collateral(wallet_address, group):
    if len(group) != 6:
        return False

    if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
        return False

    if not is_transfer(group[1]):
        return False

    if not is_transaction_sender(wallet_address, group[1]):
        return False

    if not is_app_call(group[2], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_ADD_COLLATERAL):
        return False

    if not is_app_call(group[3], APPLICATION_ID_FOLKSV2_DEPOSIT, FOLKSV2_TRANSACTION_DEPOSIT_WITHDRAW):
        return False

    return is_app_call(group[5], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SYNC_COLLATERAL)


def _is_folksv2_borrow(group):
    if len(group) != 3:
        return False

    if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
        return False

    if not is_app_call(group[1], APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER):
        return False

    return is_app_call(group[2], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_BORROW)


def _is_folksv2_repay_with_txn(wallet_address, group):
    if len(group) != 2:
        return False

    if not is_transfer(group[0]):
        return False

    if not is_transaction_sender(wallet_address, group[0]):
        return False

    return is_app_call(group[1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_REPAY_WITH_TXN)


def _is_folksv2_increase_collateral(wallet_address, group):
    length = len(group)
    if length < 5 or length > 7:
        return False

    if not is_app_call(group[-1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SYNC_COLLATERAL):
        return False

    if not is_app_call(group[-2], APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER):
        return False

    return _is_folksv2_deposit(wallet_address, group[:-2])


def _is_folksv2_reduce_collateral(group):
    if len(group) != 3:
        return False

    if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
        return False

    if not is_app_call(group[1], APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER):
        return False

    return is_app_call(group[2], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_REDUCE_COLLATERAL)


def _is_folksv2_remove_loan(group):
    if len(group) != 3:
        return False

    if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_REMOVE_COLLATERAL):
        return False

    if not is_app_call(group[1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_REMOVE_LOAN):
        return False

    return is_transfer(group[2])


def _is_folksv2_swap_collateral(wallet_address, group):
    length = len(group)
    if length < 10 or length > 12:
        return False

    if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
        return False

    if not is_app_call(group[1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SWAP_BEGIN):
        return False

    if not is_transfer(group[2]):
        return False

    if not is_transaction_sender(wallet_address, group[2]):
        return False

    if not is_transfer(group[-6]):
        return False

    if not is_transaction_sender(wallet_address, group[-6]):
        return False

    if not is_app_call(group[-5], APPLICATION_ID_FOLKSV2_POOLS, FOLKSV2_TRANSACTION_DEPOSIT):
        return False

    return is_app_call(group[-1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SWAP_END)


def _is_folksv2_swap_repay(wallet_address, group):
    if len(group) != 4:
        return False

    if not is_transfer(group[0]):
        return False

    if not is_transaction_sender(wallet_address, group[0]):
        return False

    if not is_app_call(group[1], APPLICATION_ID_DEFLEX_ORDER_ROUTER, DEFLEX_TRANSACTION_SWAP_FINALIZE):
        return False

    return _is_folksv2_repay_with_txn(wallet_address, group[2:])


def is_folksv2_transaction(wallet_address, group):
    return (_is_folksv2_deposit(wallet_address, group)
                or _is_folksv2_withdraw(group)
                or _is_folksv2_create_loan(wallet_address, group)
                or _is_folksv2_move_to_collateral(wallet_address, group)
                or _is_folksv2_borrow(group)
                or _is_folksv2_repay_with_txn(wallet_address, group)
                or _is_folksv2_swap_repay(wallet_address, group)
                or _is_folksv2_swap_collateral(wallet_address, group)
                or _is_folksv2_increase_collateral(wallet_address, group)
                or _is_folksv2_reduce_collateral(group)
                or _is_folksv2_remove_loan(group))


def handle_folksv2_transaction(wallet_address, group, exporter, txinfo):
    if _is_folksv2_deposit(wallet_address, group):
        _handle_folksv2_deposit(wallet_address, group, exporter, txinfo)

    elif _is_folksv2_withdraw(group):
        _handle_folksv2_withdraw(wallet_address, group, exporter, txinfo)

    elif _is_folksv2_create_loan(wallet_address, group):
        _handle_folksv2_fees(wallet_address, group, exporter, txinfo, COMMENT_FOLKSV2 + " create loan")

    elif _is_folksv2_move_to_collateral(wallet_address, group):
        _handle_folksv2_fees(wallet_address, group, exporter, txinfo, COMMENT_FOLKSV2 + " move to collateral")

    elif _is_folksv2_borrow(group):
        _handle_folksv2_borrow(wallet_address, group, exporter, txinfo)

    elif _is_folksv2_repay_with_txn(wallet_address, group):
        _handle_folksv2_repay_with_txn(wallet_address, group, exporter, txinfo)

    elif _is_folksv2_swap_repay(wallet_address, group):
        _handle_folksv2_swap_repay(wallet_address, group, exporter, txinfo)

    elif _is_folksv2_swap_collateral(wallet_address, group):
        _handle_folksv2_swap_collateral(wallet_address, group, exporter, txinfo)

    elif _is_folksv2_increase_collateral(wallet_address, group):
        _handle_folksv2_deposit(wallet_address, group[:-2], exporter, txinfo)

    elif _is_folksv2_reduce_collateral(group):
        _handle_folksv2_reduce_collateral(wallet_address, group, exporter, txinfo)

    elif _is_folksv2_remove_loan(group):
        _handle_folksv2_fees(wallet_address, group, exporter, txinfo, COMMENT_FOLKSV2 + " remove loan")

    else:
        export_unknown(exporter, txinfo)


def _handle_folksv2_deposit(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[-2])

    export_deposit_collateral_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_FOLKSV2)


def _handle_folksv2_withdraw(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    receive_asset = get_inner_transfer_asset(group[-1],
                                             filter=partial(is_transfer_receiver, wallet_address))

    # TODO track cost basis to calculate earnings
    export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_FOLKSV2)


def _handle_folksv2_fees(wallet_address, group, exporter, txinfo, comment):
    fee_amount = get_fee_amount(wallet_address, group)
    export_spend_fee_tx(exporter, txinfo, Algo(fee_amount), comment)


def _handle_folksv2_borrow(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    receive_asset = get_inner_transfer_asset(group[2],
                                             filter=partial(is_transfer_receiver, wallet_address))

    export_borrow_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_FOLKSV2)


def _handle_folksv2_repay_with_txn(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[0])
    receive_asset = get_inner_transfer_asset(group[1],
                                             filter=partial(is_transfer_receiver, wallet_address))
    if receive_asset is not None:
        send_asset -= receive_asset

    export_repay_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_FOLKSV2)


def _handle_folksv2_reduce_collateral(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    receive_asset = get_inner_transfer_asset(group[2],
                                             filter=partial(is_transfer_receiver, wallet_address))

    # TODO track cost basis to calculate earnings
    export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_FOLKSV2)


def _handle_folksv2_swap_repay(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group[:2])

    send_asset = get_transfer_asset(group[0])
    receive_asset = get_inner_transfer_asset(group[1],
                                             filter=partial(is_transfer_receiver, wallet_address))

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_FOLKSV2, -1)
    _handle_folksv2_repay_with_txn(wallet_address, group[2:], exporter, txinfo)


def _handle_folksv2_swap_collateral(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[2])
    receive_asset = get_transfer_asset(group[-6])

    # TODO track cost basis to calculate earnings
    export_withdraw_collateral_tx(exporter, txinfo, send_asset, 0, COMMENT_FOLKSV2, 0)
    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_FOLKSV2, 1)
    export_deposit_collateral_tx(exporter, txinfo, receive_asset, 0, COMMENT_FOLKSV2, 2)
