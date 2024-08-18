import logging
from staketaxcsv.sol.api_rpc import RpcAPI
START_EPOCH = 132  # epoch of first ever staking reward
EPOCHS_ALL = []
REFERENCE_ADDRESS_WITH_ALL_EPOCH_REWARDS = "8Vv2xVWSQtHji1Xf7Vj1vHKTa4em7zv7cAET96Vm2qt8"


def epoch_slot_and_time(epoch):
    """ Returns reward slot and timestamp for specified epoch """

    # (reward slot of first epoch with rewards) + num_epochs * slots_per_epoch
    slot = 57456000 + (epoch - START_EPOCH) * 432000

    # Find first valid slot starting from first guess
    for i in range(5):
        try:
            logging.info("Seeing if slot=%s is valid ...", slot)
            timestamp = RpcAPI.get_block_time(slot)
            return slot, timestamp
        except KeyError as e:
            slot += 4

    raise Exception(f"Unable to find valid slot/timestamp for epoch={epoch}")


def get_epochs_all():
    global EPOCHS_ALL
    if not EPOCHS_ALL:
        end_epoch = RpcAPI.get_latest_epoch()
        EPOCHS_ALL = list(range(START_EPOCH, end_epoch))
    return EPOCHS_ALL
