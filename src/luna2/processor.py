
import common.ibc.handle
import common.ibc.processor
from luna2.config_luna2 import localconfig
from luna2 import constants as co
from settings_csv import LUNA2_LCD_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, "dummy", co.EXCHANGE_LUNA2, localconfig.ibc_addresses, LUNA2_LCD_NODE)

    for msginfo in txinfo.msgs:
        # Handle common messages
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        # Handle unknown messages
        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
