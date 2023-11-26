import logging
from staketaxcsv.sol.api_rpc import RpcAPI
START_EPOCH = 132  # epoch of first ever staking reward
EPOCHS_ALL = []


def slot_to_timestamp(slot):
    slot = str(slot)

    logging.info("Fetching block time for slot=%s", slot)
    timestamp = RpcAPI.get_block_time(slot)

    return timestamp


def get_epochs_all():
    global EPOCHS_ALL
    if not EPOCHS_ALL:
        end_epoch = RpcAPI.get_latest_epoch()
        EPOCHS_ALL = list(range(START_EPOCH, end_epoch))
    return EPOCHS_ALL
