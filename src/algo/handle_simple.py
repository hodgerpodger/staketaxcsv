from common.make_tx import make_reward_tx, make_unknown_tx


def handle_unknown(exporter, txinfo):
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)


def handle_participation_rewards(reward, exporter, txinfo):
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        row.fee = 0
        row.comment = "Participation Rewards"
        exporter.ingest_row(row)
