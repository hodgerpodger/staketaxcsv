
# staketaxcsv

* Python repository to create blockchain CSVs for Akash (AKT), Algorand (ALGO), Archway (ARCH), Cosmos (ATOM), 
  Agoric (BLD), Bitsong (BTSG), Sentinel (DVPN), dYdX (DYDX), Dymension (DYM), Evmos (EVMOS), Fetch.ai (FET),
  Gravity Bridge (GRAV), Chihuahua (HUAHUA), IoTex (IOTX), Injective (INJ), Juno (JUNO), Kujira (KUJI), 
  KYVE Network (KYVE), Terra Classic (LUNC), Terra 2.0 (LUNA), Neutron (NTRN), Nolus Protocol (NLS), Osmosis (OSMO),
  Solana (SOL), Stargaze (STARS), Stride (STRD), and Celestia (TIA). 
* CSV codebase for <https://stake.tax>
* Contributions/PRs highly encouraged, such as support for new txs, blockchains, or CSV formats.  Examples:
  * Add cosmo-based-blockchain CSV: https://docs.stake.tax/devs/adding-csv-in-cosmos-based-ecosystem
  * Add new CSV format: https://docs.stake.tax/devs/add-new-csv-format-example
  

# Install

  1. Install python 3.9 ([one way](README_reference.md#installing-python-39-on-macos))
  1. Install pip packages

     ```
     pip3 install -r requirements.txt
     ```
  
# Usage

* Load environment variables (add to ~/.bash_profile or ~/.bashrc to avoid doing every time):
  
  ```
  set -o allexport
  source sample.env
  set +o allexport
  ```

* Usage as CLI
  * See [PYTHONPATH issues](README_reference.md#PYTHONPATH-issues) if encountering import errors.
  * Same arguments apply for report_algo.py (ALGO), ..., report_*.py:
  
  ```sh
  cd src
  
  # Create default CSV
  python3 staketaxcsv/report_osmo.py <wallet_address>
  
  # Create all CSV formats (i.e. koinly, cointracking, etc.)
  python3 staketaxcsv/report_osmo.py <wallet_address> --format all
  
  # Show CSV result for single transaction (great for development/debugging)
  python3 staketaxcsv/report_osmo.py <wallet_address> --txid <txid>
  
  # Show CSV result for single transaction in debug mode (great for development/debugging)
  python3 staketaxcsv/report_osmo.py <wallet_address> --txid <txid> --debug

  # Create historical balances CSV
  python3 staketaxcsv/report_osmo.py <wallet_address> --historical
  
  # Create cosmos+ CSV
  python3 staketaxcsv/report_cosmosplus <wallet_address> --cosmosplus_node <url_lcd_node> --cosmosplus_ticker <token_symbol>
  ```

* Usage as staketaxcsv module: see [Usage as staketaxcsv module](README_reference.md#usage-as-staketaxcsv-module)

# Contributing Code

* See [Tests](README_reference.md#tests) for running unit tests.
* See [Linting](README_reference.md#linting) to see code style feedback.
* See [Docker](README_reference.md#docker) to alternatively install/run in docker container.

# Reference

See [README_reference.md](README_reference.md):

* [Linting](README_reference.md#linting)
* [Tests](README_reference.md#tests)
* [Usage as staketaxcsv module](README_reference.md#usage-as-staketaxcsv-module)
* [Docker](README_reference.md#docker)
* [PYTHONPATH Issues](README_reference.md#pythonpath-issues)
* [Run CSV job with no transaction limit](README_reference.md#run-csv-job-with-no-transaction-limit)
* [Ideal Configuration](README_reference.md#ideal-configuration)
  * [RPC Node Settings](README_reference.md#rpc-node-settings)
  * [DB Cache](README_reference.md#db-cache)
* [Installing python 3.9.9 on macOS](README_reference.md#installing-python-39-on-macos)
