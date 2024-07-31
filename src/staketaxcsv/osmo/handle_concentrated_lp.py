import logging
from collections import defaultdict
from staketaxcsv.osmo import util_osmo
from staketaxcsv.osmo.handle_lp import LockedTokens
from staketaxcsv.osmo.handle_unknown import handle_unknown_detect_transfers
from staketaxcsv.osmo.make_tx import (
    make_osmo_lp_deposit_tx, make_osmo_lp_withdraw_tx, make_osmo_reward_tx, make_osmo_simple_tx)


class PositionLiquidity:

    liquidities = defaultdict(float)  # <position_id> -> <liquidity>

    @classmethod
    def create_position(cls, position_id, liquidity):
        assert (position_id not in cls.liquidities)
        cls.liquidities[position_id] = liquidity

    @classmethod
    def add_to_position(cls, old_position_id, new_position_id, new_position_liquidity):
        liquidity_added = new_position_liquidity - cls.liquidities[old_position_id]

        # Close liquidity of old position id
        cls.liquidities[old_position_id] = 0

        # Write new liquidity to new position id
        cls.liquidities[new_position_id] = new_position_liquidity

        return liquidity_added

    @classmethod
    def withdraw_position(cls, position_id, liquidity):
        assert (position_id in cls.liquidities)

        cls.liquidities[position_id] -= liquidity

        if cls.liquidities[position_id] == 0:
            del cls.liquidities[position_id]


def _lp_currency(pool_id):
    return "LP_POOL_ID_" + pool_id


def handle_create_position(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    events_by_type = msginfo.events_by_type

    if len(transfers_out) == 2:
        create_position = events_by_type["create_position"]
        pool_id = create_position["pool_id"]
        position_id = create_position["position_id"]
        liquidity = float(create_position["liquidity"])

        lp_amount = liquidity
        lp_currency = _lp_currency(pool_id)
        sent_amount1, sent_currency1 = transfers_out[0]
        sent_amount2, sent_currency2 = transfers_out[1]

        PositionLiquidity.create_position(position_id, liquidity)

        comment = f"concentrated_lp.create_position [pool_id={pool_id}][position_id={position_id}] "
        rows = [
            make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount1, sent_currency1, lp_amount / 2, lp_currency),
            make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount2, sent_currency2, lp_amount / 2, lp_currency),
        ]
        util_osmo._ingest_rows(exporter, rows, comment)
        return
    elif len(transfers_out) == 1:
        create_position = events_by_type["create_position"]
        pool_id = create_position["pool_id"]
        position_id = create_position["position_id"]
        liquidity = float(create_position["liquidity"])

        lp_amount = liquidity
        lp_currency = _lp_currency(pool_id)
        sent_amount1, sent_currency1 = transfers_out[0]

        PositionLiquidity.create_position(position_id, liquidity)
        comment = f"concentrated_lp.create_position [pool_id={pool_id}][position_id={position_id}] "
        rows = [
            make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount1, sent_currency1, lp_amount, lp_currency),
        ]
        util_osmo._ingest_rows(exporter, rows, comment)
        return

    raise Exception("Unable to handle tx in handle_create_position()")


def handle_add_to_position(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net
    events_by_type = msginfo.events_by_type

    if len(transfers_in) <= 1 and len(transfers_out) == 2:
        withdraw_position_id = events_by_type["withdraw_position"]["position_id"]
        withdraw_pool_id = events_by_type["withdraw_position"]["pool_id"]

        create_position_id = events_by_type["create_position"]["position_id"]
        create_liquidity = float(events_by_type["create_position"]["liquidity"])
        create_pool_id = events_by_type["create_position"]["pool_id"]

        assert (withdraw_pool_id == create_pool_id)

        liquidity_added = PositionLiquidity.add_to_position(withdraw_position_id, create_position_id, create_liquidity)

        lp_amount = liquidity_added
        lp_currency = _lp_currency(create_pool_id)

        sent_amount1, sent_currency1 = transfers_out[0]
        sent_amount2, sent_currency2 = transfers_out[1]

        comment = f"concentrated_lp.add_to_position [pool_id={create_pool_id}]" + \
                  f"[old position_id={withdraw_position_id}][new position_id={create_position_id}] "

        rows = [
            make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount1, sent_currency1, lp_amount / 2, lp_currency),
            make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount2, sent_currency2, lp_amount / 2, lp_currency),
        ]
        util_osmo._ingest_rows(exporter, rows, comment)

        # Handle extra reward if exists
        if len(transfers_in) == 1:
            tokens_out = events_by_type.get("collect_incentives", {}).get("tokens_out", None)
            # i.e. 1268498uosmo
            amt, cur = msginfo.amount_currency(tokens_out)[0]
            row = make_osmo_reward_tx(txinfo, msginfo, amt, cur)
            util_osmo._ingest_rows(exporter, [row], comment)

        return

    raise Exception("Unable to handle tx in handle_add_to_position()")


def handle_collect_incentives(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net
    events_by_type = msginfo.events_by_type

    if len(transfers_in) > 0 and len(transfers_out) == 0:
        position_id = events_by_type["collect_incentives"]["position_id"]
        comment = f"concentrated_lp.collect_incentives [position_id={position_id}]"

        rows = []
        for received_amount, received_currency in transfers_in:
            row = make_osmo_reward_tx(txinfo, msginfo, received_amount, received_currency)
            rows.append(row)
        util_osmo._ingest_rows(exporter, rows, comment)
        return

    raise Exception("Unable to handle tx in handle_collect_incentives()")


def handle_collect_spread_rewards(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net
    events_by_type = msginfo.events_by_type

    if len(transfers_in) > 0 and len(transfers_out) == 0:
        position_id = events_by_type["collect_spread_rewards"]["position_id"]
        comment = f"concentrated_lp.collect_spread_rewards [position_id={position_id}]"

        rows = []
        for received_amount, received_currency in transfers_in:
            row = make_osmo_reward_tx(txinfo, msginfo, received_amount, received_currency)
            rows.append(row)
        util_osmo._ingest_rows(exporter, rows, comment)
        return

    raise Exception("Unable to handle tx in handle_collect_spread_rewards()")


def handle_withdraw_position(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net
    events_by_type = msginfo.events_by_type

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        position_id = events_by_type["withdraw_position"]["position_id"]
        liquidity = abs(float(events_by_type["withdraw_position"]["liquidity"]))
        pool_id = events_by_type["withdraw_position"]["pool_id"]

        lp_amount = liquidity
        lp_currency = _lp_currency(pool_id)

        receive_amount, receive_currency = transfers_in[0]

        PositionLiquidity.withdraw_position(position_id, liquidity)

        comment = f"concentrated_lp.withdraw_position [pool_id={pool_id}][position_id={position_id}] "
        rows = [
            make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount, lp_currency, receive_amount, receive_currency)
        ]
        util_osmo._ingest_rows(exporter, rows, comment)
        return

    if len(transfers_in) == 2 and len(transfers_out) == 0:
        position_id = events_by_type["withdraw_position"]["position_id"]
        liquidity = abs(float(events_by_type["withdraw_position"]["liquidity"]))
        pool_id = events_by_type["withdraw_position"]["pool_id"]

        lp_amount = liquidity
        lp_currency = _lp_currency(pool_id)

        receive_amount1, receive_currency1 = transfers_in[0]
        receive_amount2, receive_currency2 = transfers_in[1]

        PositionLiquidity.withdraw_position(position_id, liquidity)

        comment = f"concentrated_lp.withdraw_position [pool_id={pool_id}][position_id={position_id}] "
        rows = [
            make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount / 2, lp_currency, receive_amount1, receive_currency1),
            make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount / 2, lp_currency, receive_amount2, receive_currency2),
        ]
        util_osmo._ingest_rows(exporter, rows, comment)
        return

    if len(transfers_in) == 3 and len(transfers_out) == 0:
        position_id = events_by_type["withdraw_position"]["position_id"]
        liquidity = abs(float(events_by_type["withdraw_position"]["liquidity"]))
        pool_id = events_by_type["withdraw_position"]["pool_id"]

        lp_amount = liquidity
        lp_currency = _lp_currency(pool_id)

        receive_amount1, receive_currency1 = transfers_in[0]
        receive_amount2, receive_currency2 = transfers_in[1]
        receive_amount3, receive_currency3 = transfers_in[2]

        PositionLiquidity.withdraw_position(position_id, liquidity)

        comment = f"concentrated_lp.withdraw_position [pool_id={pool_id}][position_id={position_id}] "
        rows = [
            make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount / 3, lp_currency, receive_amount1, receive_currency1),
            make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount / 3, lp_currency, receive_amount2, receive_currency2),
            make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount / 3, lp_currency, receive_amount3, receive_currency3),
        ]
        util_osmo._ingest_rows(exporter, rows, comment)
        return

    raise Exception("Unable to handle tx in handle_withdraw_position()")


def handle_migrate_to_concentrated(exporter, txinfo, msginfo):
    wallet_address = txinfo.wallet_address
    transfers_in, transfers_out = msginfo.transfers
    events_by_type = msginfo.events_by_type

    # Find lp token/amount
    lp_amount, lp_currency = _find_lp_token_amount(transfers_in)
    if lp_currency is None:
        logging.error("Unable to find lp token/amount")
        handle_unknown_detect_transfers(exporter, txinfo, msginfo)
        return

    # Save leaving old pool info
    lock_id = msginfo.message["lock_id"]
    LockedTokens.remove_stake(wallet_address, lock_id)

    # Save entering new pool info
    create_position = events_by_type["create_position"]
    pool_id = create_position["pool_id"]
    position_id = create_position["position_id"]
    liquidity = float(create_position["liquidity"])

    PositionLiquidity.create_position(position_id, liquidity)

    row = make_osmo_simple_tx(txinfo, msginfo)
    row.comment += "concentrated_lp.migrate"
    row.comment += f"[exit lock_id={lock_id}]"
    row.comment += f"[enter pool_id={pool_id} position_id={position_id}]"
    exporter.ingest_row(row)
    return


def _find_lp_token_amount(transfers):
    for amount, currency in transfers:
        if currency.startswith("GAMM-"):
            return amount, currency

    return None, None
