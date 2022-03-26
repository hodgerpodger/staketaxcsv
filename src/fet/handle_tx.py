import common.ibc.handle
import common.ibc.processor
from fet.config_fet import localconfig


def handle_tx(exporter, txinfo):
    for msginfo in txinfo.msgs:
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
