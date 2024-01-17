import staketaxcsv.atom.constants as co
import staketaxcsv.atom.cosmoshub123.processor_1
import staketaxcsv.atom.cosmoshub123.processor_2
import staketaxcsv.atom.cosmoshub123.processor_3
import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
from staketaxcsv.atom.config_atom import localconfig
from staketaxcsv.settings_csv import ATOM_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def _is_legacy_format_cosmoshub1(elem):
    if elem.get("chain_id", "") == "cosmoshub-1":
        return True

    return "value" in elem["tx"] and "logs" not in elem


def _is_legacy_format_cosmoshub2(elem):
    if elem.get("chain_id", "") == "cosmoshub-2":
        return True

    return "value" in elem["tx"] and "logs" in elem and elem["logs"] and "events" not in elem["logs"][0]


def _is_legacy_format_cosmoshub3(elem):
    if elem.get("chain_id", "") == "cosmoshub-3":
        return True

    return "value" in elem["tx"] and "logs" in elem and elem["logs"] and "events" in elem["logs"][0]


def process_tx(wallet_address, elem, exporter):
    if _is_legacy_format_cosmoshub1(elem):
        staketaxcsv.atom.cosmoshub123.processor_1.process_tx(wallet_address, elem, exporter)
        return
    if _is_legacy_format_cosmoshub2(elem):
        staketaxcsv.atom.cosmoshub123.processor_2.process_tx(wallet_address, elem, exporter)
        return
    if _is_legacy_format_cosmoshub3(elem):
        staketaxcsv.atom.cosmoshub123.processor_3.process_tx(wallet_address, elem, exporter)
        return

    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_ATOM, ATOM_NODE
    )

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
