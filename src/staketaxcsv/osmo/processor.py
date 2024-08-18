import logging

import staketaxcsv.common.ibc.processor
import staketaxcsv.osmo.handle_concentrated_lp
import staketaxcsv.osmo.handle_general
import staketaxcsv.osmo.handle_lp
import staketaxcsv.osmo.handle_staking
import staketaxcsv.osmo.handle_superfluid
import staketaxcsv.osmo.handle_swap
import staketaxcsv.osmo.handle_unknown
from staketaxcsv.osmo import constants as co
from staketaxcsv.osmo import util_osmo
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo.MsgInfoOsmo import MsgInfoOsmo
from staketaxcsv.settings_csv import OSMO_NODE
from staketaxcsv.common.ibc.api_lcd_cosmwasm import contract_label
import staketaxcsv.osmo.contracts.icns
import staketaxcsv.osmo.contracts.liquid
import staketaxcsv.osmo.contracts.mars_credit_manager
import staketaxcsv.osmo.contracts.mars_red_bank
import staketaxcsv.osmo.contracts.quasar
CONTRACT_ICNS_REGISTRAR = "osmo1llh07xn7pcst3jqm0xpsucf90lzugfskkkhk8a3u2yznqmse4l5smydwpw"
CONTRACT_ICNS_RESOLVER = "osmo1xk0s8xgktn9x5vwcgtjdxqzadg88fgn33p8u9cnpdxwemvxscvast52cdd"
CONTRACT_LIQUID_STAKE = "osmo1f5vfcph2dvfeqcqkhetwv75fda69z7e5c2dldm3kvgj23crkv6wqcn47a0"
CONTRACT_MARS_CREDIT_MANAGER = "osmo1f2m24wktq0sw3c0lexlg7fv4kngwyttvzws3a3r3al9ld2s2pvds87jqvf"
CONTRACT_MARS_INCENTIVES = "osmo1nkahswfr8shg8rlxqwup0vgahp0dk4x8w6tkv3rra8rratnut36sk22vrm"
CONTRACT_MARS_RED_BANK = "osmo1c3ljch9dfw5kf52nfwpxd2zmj2ese7agnx0p9tenkrryasrle5sqf3ftpg"
CONTRACT_QUASAR_VAULT = "osmo15uk8m3wchpee8gjl02lwelxlsl4uuy3pdy7u6kz7cu7krlph2xpscf53cy"


def process_txs(wallet_address, elems, exporter):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_OSMO, OSMO_NODE, MsgInfoOsmo)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        _handle_message(exporter, txinfo, msginfo)

    return txinfo


def _handle_message(exporter, txinfo, msginfo):
    try:
        msg_type = util_osmo._msg_type(msginfo)

        # swaps
        if msg_type == co.MSG_TYPE_SWAP_IN:
            staketaxcsv.osmo.handle_swap.handle_swap(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_SPLIT_ROUTE_SWAP:
            staketaxcsv.osmo.handle_swap.handle_swap(exporter, txinfo, msginfo)

        # lp transactions
        elif msg_type == co.MSG_TYPE_JOIN_POOL:
            staketaxcsv.osmo.handle_lp.handle_lp_deposit(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_JOIN_SWAP_EXTERN_AMOUNT_IN:
            staketaxcsv.osmo.handle_lp.handle_lp_deposit_partial(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_EXIT_POOL:
            staketaxcsv.osmo.handle_lp.handle_lp_withdraw(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LOCK_TOKENS:
            staketaxcsv.osmo.handle_lp.handle_lp_stake(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_BEGIN_UNLOCKING:
            staketaxcsv.osmo.handle_lp.handle_lp_unstake(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_UNLOCK_PERIOD_LOCK:
            staketaxcsv.osmo.handle_lp.handle_unlock_period_lock(exporter, txinfo, msginfo)

        # superfluid
        elif msg_type == co.MSG_TYPE_SUPERFLUID_DELEGATE:
            staketaxcsv.osmo.handle_superfluid.handle_delegate(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LOCK_AND_SUPERFLUID_DELEGATE:
            staketaxcsv.osmo.handle_superfluid.handle_lp_stake(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_SUPERFLUID_UNDELEGATE, co.MSG_TYPE_SUPERFLUID_UNBOND_LOCK]:
            staketaxcsv.osmo.handle_superfluid.handle_undelegate_or_unbond(exporter, txinfo, msginfo)

        # concentrated liquidity
        elif msg_type == co.MSG_TYPE_CREATE_POSITION:
            staketaxcsv.osmo.handle_concentrated_lp.handle_create_position(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_ADD_TO_POSITION:
            staketaxcsv.osmo.handle_concentrated_lp.handle_add_to_position(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_COLLECT_INCENTIVES:
            staketaxcsv.osmo.handle_concentrated_lp.handle_collect_incentives(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_COLLECT_SPREAD_REWARDS:
            staketaxcsv.osmo.handle_concentrated_lp.handle_collect_spread_rewards(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_WITHDRAW_POSITION:
            staketaxcsv.osmo.handle_concentrated_lp.handle_withdraw_position(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_UNLOCK_AND_MIGRATE_SHARES_TO_FULL_RANGE_CONCENTRATED_POSITION:
            staketaxcsv.osmo.handle_concentrated_lp.handle_migrate_to_concentrated(exporter, txinfo, msginfo)

        # execute contract
        elif msg_type == co.MSG_TYPE_EXECUTE_CONTRACT:
            _handle_execute_contract(exporter, txinfo, msginfo)

        else:
            staketaxcsv.osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
    except Exception as e:
        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        staketaxcsv.osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

        if localconfig.debug:
            raise e

    return txinfo


def _handle_execute_contract(exporter, txinfo, msginfo):
    contract = msginfo.contract

    if contract == CONTRACT_LIQUID_STAKE:
        staketaxcsv.osmo.contracts.liquid.handle_liquid_stake(exporter, txinfo, msginfo)

    # mars
    elif contract == CONTRACT_MARS_INCENTIVES:
        staketaxcsv.osmo.contracts.mars_credit_manager.handle_claim_rewards(exporter, txinfo, msginfo)
    elif contract == CONTRACT_MARS_CREDIT_MANAGER:
        staketaxcsv.osmo.contracts.mars_credit_manager.handle_credit_manager(exporter, txinfo, msginfo)
    elif contract == CONTRACT_MARS_RED_BANK:
        staketaxcsv.osmo.contracts.mars_red_bank.handle_red_bank(exporter, txinfo, msginfo)

    # icns
    elif contract in [CONTRACT_ICNS_REGISTRAR, CONTRACT_ICNS_RESOLVER]:
        staketaxcsv.osmo.contracts.icns.handle(exporter, txinfo, msginfo)

    else:
        label = contract_label(contract, localconfig, OSMO_NODE)

        if label.startswith("quasar-cl-vault-"):
            staketaxcsv.osmo.contracts.quasar.handle(exporter, txinfo, msginfo)
        else:
            staketaxcsv.osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
