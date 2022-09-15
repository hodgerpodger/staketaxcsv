import staketaxcsv.common.ibc.api_lcd
import staketaxcsv.luna2.constants as co
from staketaxcsv.luna2.make_tx import make_genesis_airdrop1_tx
from staketaxcsv.settings_csv import LUNA2_LCD_NODE


def genesis_airdrop(wallet_address, exporter):
    amount_luna = _genesis_airdrop_luna_amount(wallet_address)
    if amount_luna:
        row = make_genesis_airdrop1_tx(amount_luna, wallet_address)
        exporter.ingest_row(row)


def _genesis_airdrop_luna_amount(wallet_address):
    data = staketaxcsv.common.ibc.api_lcd.LcdAPI(LUNA2_LCD_NODE).balances(wallet_address, height=1)
    balances_elem = data["balances"]

    if len(balances_elem) == 0:
        return 0

    denom = balances_elem[0]["denom"]
    amount_string = balances_elem[0]["amount"]
    assert (denom == "uluna")
    return float(amount_string) / co.MILLION
