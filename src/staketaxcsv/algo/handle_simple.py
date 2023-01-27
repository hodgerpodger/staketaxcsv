from staketaxcsv.algo.export_tx import export_reward_tx
from staketaxcsv.common.make_tx import make_unknown_tx


def handle_unknown(exporter, txinfo):
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)


def handle_participation_rewards(reward, exporter, txinfo):
    export_reward_tx(exporter, txinfo, reward, comment="Participation Rewards")
