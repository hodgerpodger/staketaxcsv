from common.ErrorCounter import ErrorCounter
from common.ExporterTypes import TX_TYPE_NFT_WHITELIST
from terra import util_terra
from terra.api_lcd import LcdAPI
from terra.constants import MILLION
from terra.handle_simple import handle_simple, handle_unknown
from terra.make_tx import (
    make_nft_buy_tx,
    make_nft_deposit,
    make_nft_mint_no_purchase_tx,
    make_nft_mint_tx,
    make_nft_offer_sell_tx,
    make_nft_reserve_tx,
    make_nft_transfer_in_tx,
    make_nft_transfer_out_tx,
    make_nft_withdraw,
)


def handle_add_whitelist(exporter, elem, txinfo):
    handle_simple(exporter, txinfo, TX_TYPE_NFT_WHITELIST)


def handle_add_to_deposit(exporter, elem, txinfo):
    """ Hero mint website deposit to purchase nft """
    wallet_address = txinfo.wallet_address
    transfer = elem["logs"][0]["events_by_type"]["transfer"]

    amount_string = transfer["amount"][0]
    sender = transfer["sender"][0]
    sent_amount, sent_currency = util_terra._amount(amount_string)
    row = make_nft_deposit(txinfo, sent_amount, sent_currency)
    exporter.ingest_row(row)

    assert(sender == wallet_address)


def handle_accept_deposit(exporter, elem, txinfo):
    """ Hero mint website receive nft after deposit """
    handle_unknown(exporter, txinfo)


def handle_reserve_nft(exporter, elem, txinfo):
    """ nft mint for randomearth.io assets (or just the reservation that is only history for wallet) """

    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    inserted_row = False
    execute_msgs = util_terra._execute_msgs(elem)
    contracts = util_terra._contracts(elem)

    for i in range(len(execute_msgs)):
        execute_msg = execute_msgs[i]
        contract = contracts[i]

        if "reserve_nft" in execute_msg and execute_msg["reserve_nft"]["reservation_owner"] == wallet_address:
            payment = execute_msg["reserve_nft"]["payment"]
            sent_amount, sent_currency = _parse_asset(payment)
            name = _nft_name(contract)

            row = make_nft_reserve_tx(txinfo, sent_amount, sent_currency, name)
            exporter.ingest_row(row)
            inserted_row = True

    if not inserted_row:
        ErrorCounter.increment("handle_reserve_nft", txid)
        handle_unknown(exporter, txinfo)


def _parse_asset(asset):
    amount_string = asset["amount"]

    info = asset["info"]
    if "nft" in info:
        token_id = info["nft"]["token_id"]
        contract_addr = info["nft"]["contract_addr"]
        nft_currency = "{}_{}".format(contract_addr, token_id)
        return 1, nft_currency
    elif "native_token" in info:
        denom = info["native_token"]["denom"]
        if denom.startswith("u"):
            amount = float(amount_string) / MILLION
            currency = denom[1:]
            currency = currency.upper()
            return amount, currency

    raise Exception("_parse_asset(): Unable to handle asset {}".format(asset))


def handle_mint_nft(exporter, elem, txinfo):
    """ nft mint for randomearth.io assets """
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    inserted_row = False
    execute_msgs = util_terra._execute_msgs(elem)
    contracts = util_terra._contracts(elem)

    for i in range(len(execute_msgs)):
        execute_msg = execute_msgs[i]
        contract = contracts[i]

        if "mint_nft" in execute_msg and execute_msg["mint_nft"]["token_owner"] == wallet_address:
            mint_nft = execute_msg["mint_nft"]
            token_id = mint_nft["token_id"]
            nft_currency = "{}_{}".format(contract, token_id)
            name = _nft_name(contract)

            row = make_nft_mint_no_purchase_tx(txinfo, nft_currency, name)
            exporter.ingest_row(row)
            inserted_row = True

    if not inserted_row:
        ErrorCounter.increment("handle_mint_nft", txid)
        handle_unknown(exporter, txinfo)


def handle_purchase_nft(exporter, elem, txinfo):
    # mint nft of styllar
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    inserted_row = False
    logs = elem["logs"]
    for log in logs:
        events_by_type = log["events_by_type"]
        from_contract = events_by_type.get("from_contract", None)
        if from_contract:
            contract = from_contract["sender"][0]
            token_id = from_contract["token_id"][0]
            coin_spent = events_by_type["coin_spent"]
            sent_amount, sent_currency = _coin_spent(coin_spent, wallet_address)
            nft_currency = "{}_{}".format(contract, token_id)

            if sent_amount:
                name = _nft_name(contract)
                row = make_nft_mint_tx(txinfo, sent_amount, sent_currency, nft_currency, name)
                exporter.ingest_row(row)
                inserted_row = True

    if not inserted_row:
        ErrorCounter.increment("handle_purchase_nft", txid)
        handle_unknown(exporter, txinfo)


def _coin_spent(coin_spent, wallet_address):
    amount_strings = coin_spent["amount"]
    spenders = coin_spent["spender"]

    for i in range(len(amount_strings)):
        amount_string = amount_strings[i]
        spender = spenders[i]
        if spender == wallet_address:
            sent_amount, sent_currency = util_terra._amount(amount_string)
            return sent_amount, sent_currency

    return None, None


cache_names = {}


def _nft_name(contract):
    if contract in cache_names:
        return cache_names[contract]

    data = LcdAPI.contract_info(contract)

    try:
        init_msg = data["result"]["init_msg"]
        name = init_msg.get("collection_name", None)
        if not name:
            name = init_msg.get("name")
    except Exception:
        name = ""

    cache_names[contract] = name
    return name


def handle_transfer_nft(exporter, elem, txinfo, index=0):
    """ nft transfer for randomearth.io assets """
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    from_contract = elem["logs"][index]["events_by_type"]["from_contract"]
    contract = from_contract["contract_address"][0]
    recipient = from_contract["recipient"][0]
    sender = from_contract["sender"][0]
    token_id = from_contract["token_id"][0]
    nft_currency = "{}_{}".format(contract, token_id)
    name = _nft_name(contract)

    if recipient == wallet_address:
        row = make_nft_transfer_in_tx(txinfo, nft_currency, name)
        exporter.ingest_row(row)
    elif sender == wallet_address:
        row = make_nft_transfer_out_tx(txinfo, nft_currency, name)
        exporter.ingest_row(row)
    else:
        ErrorCounter.increment("handle_transfer_nft", txid)
        handle_unknown(exporter, txinfo)


def handle_send_nft(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address

    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]
    token_id = from_contract["token_id"][0]
    sender = from_contract["sender"][0]
    contract = from_contract["contract_address"][0]
    action = from_contract["action"][0]

    if action == "send_nft" and sender == wallet_address:
        nft_currency = "{}_{}".format(contract, token_id)
        name = _nft_name(contract)
        row = make_nft_transfer_out_tx(txinfo, nft_currency, name)
        exporter.ingest_row(row)
    else:
        handle_unknown(exporter, txinfo)


def handle_approve(exporter, elem, txinfo):
    """ nft post order (not sale) on randomearth.io """
    txid = txinfo.txid
    if _is_offer_sell(elem):
        msgs = elem["tx"]["value"]["msg"]
        contract = msgs[0]["value"]["contract"]
        deposit_asset = msgs[1]["value"]["execute_msg"]["deposit"]["asset"]
        _, nft_currency = _parse_asset(deposit_asset)
        taker_asset = msgs[2]["value"]["execute_msg"]["post_order"]["order"]["order"]["taker_asset"]
        offer_amount, offer_currency = _parse_asset(taker_asset)
        name = _nft_name(contract)

        row = make_nft_offer_sell_tx(txinfo, nft_currency, offer_amount, offer_currency, name)
        exporter.ingest_row(row)

    else:
        ErrorCounter.increment("approve", txid)
        handle_unknown(exporter, txinfo)


def _is_offer_sell(elem):
    keys = util_terra._execute_msgs_keys(elem)

    if (len(keys) == 3
       and keys[0] == "approve"
       and keys[1] == "deposit"
       and keys[2] == "post_order"):
        return True
    else:
        return False


def handle_execute_order(exporter, elem, txinfo):
    """ nft buy on randomearth.io """
    txid = txinfo.txid

    inserted_row = False
    for execute_msg in util_terra._execute_msgs(elem):
        if "execute_order" in execute_msg:
            order = execute_msg["execute_order"]["order"]["order"]
            maker_asset = order["maker_asset"]
            taker_asset = order["taker_asset"]

            _, nft_currency = _parse_asset(maker_asset)
            sent_amount, sent_currency = _parse_asset(taker_asset)
            collection_contract = maker_asset["info"]["nft"]["contract_addr"]
            name = _nft_name(collection_contract)

            row = make_nft_buy_tx(txinfo, sent_amount, sent_currency, nft_currency, name)
            exporter.ingest_row(row)
            inserted_row = True

    if not inserted_row:
        ErrorCounter.increment("approve", txid)
        handle_unknown(exporter, txinfo)


def handle_withdraw(exporter, elem, txinfo, index=0):
    """ withdraw nft or sell proceeds from randomearth.io """
    wallet_address = txinfo.wallet_address
    execute_msg = util_terra._execute_msg(elem)

    # Check if wallet is sender (can be receiver of later transfer_nft msg)
    sender = elem["tx"]["value"]["msg"][index]["value"]["sender"]
    if sender == wallet_address:
        asset = execute_msg["withdraw"]["asset"]
        received_amount, received_currency = _parse_asset(asset)
        row = make_nft_withdraw(txinfo, received_amount, received_currency)
        exporter.ingest_row(row)
