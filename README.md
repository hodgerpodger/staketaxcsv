
# staketaxcsv

* Python repository to create blockchain CSVs for Algorand (ALGO), Cosmos (ATOM), Agoric (BLD), Bitsong (BTSG),
  Sentinel (DVPN), Evmos (EVMOS), Fetch.ai (FET), Chihuahua (HUAHUA), IoTex (IOTX), Juno (JUNO), Kujira (KUJI),
  Terra Classic (LUNC), Terra 2.0 (LUNA), Osmosis (OSMO), Solana (SOL), and Stargaze (STARS) blockchains. 
* CSV codebase for <https://stake.tax>
* Contributions/PRs highly encouraged, such as support for new txs, blockchains, or CSV formats.  Examples:
  * Add cosmo-based-blockchain CSV (i.e. Agoric): [commit](https://github.com/hodgerpodger/staketaxcsv/commit/ff8af30b85ea4416504d043723e91f3edf5c7ee1).
    * Simply use latest main versions of each file and that's basically it
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
  * Remember to add your path to *staketaxcsv/src* to the `PYTHONPATH` environment variable.
  * Same arguments apply for report_algo.py (ALGO), report_atom.py (ATOM), report_*.py:
  
  ```sh
  cd src
  
  # Create default CSV
  python3 staketaxcsv/report_atom.py <wallet_address>
  
  # Create all CSV formats (i.e. koinly, cointracking, etc.)
  python3 staketaxcsv/report_atom.py <wallet_address> --format all
  
  # Show CSV result for single transaction (great for development/debugging)
  python3 staketaxcsv/report_atom.py <wallet_address> --txid <txid>
  
  # Show CSV result for single transaction in debug mode (great for development/debugging)
  python3 staketaxcsv/report_atom.py <wallet_address> --txid <txid> --debug
  ```

* Usage as staketaxcsv module

  ```
    >>> import staketaxcsv
    >>> help(staketaxcsv.api)
    >>>
    >>> address = "<SOME_ADDRESS>"
    >>> txid = "<SOME_TXID>"
    >>>
    >>> staketaxcsv.formats()
    ['default', 'balances', 'accointing', 'bitcointax', 'coinledger', 'coinpanda', 'cointelli', 'cointracking', 'cointracker', 'cryptio', 'cryptocom', 'cryptotaxcalculator', 'cryptoworth', 'koinly', 'recap', 'taxbit', 'tokentax', 'zenledger']
    >>>
    >>> staketaxcsv.tickers()
    ['ALGO', 'ATOM', 'BLD', 'BTSG', 'DVPN', 'EVMOS', 'FET', 'HUAHUA', 'IOTX', 'JUNO', 'KUJI', 'LUNA1', 'LUNA2', 'OSMO', 'REGEN', 'SOL', 'STARS']
    >>>
    >>> # write single transaction CSV
    >>> staketaxcsv.transaction("ATOM", address, txid, "koinly")
    ...
    >>> # write koinly CSV
    >>> staketaxcsv.csv("ATOM", address, "koinly")
    ...
    >>> # write all CSVs (koinly, cointracking, etc.)
    >>> staketaxcsv.csv_all("ATOM", address)
    ...
    >>> # check address is valid
    >>> staketaxcsv.has_csv("ATOM", address)
    True
  ```


# Docker

See [Docker](README_reference.md#docker) to alternatively install/run in docker container.

# Contributing Code

* See [Linting](README_reference.md#linting) to see code style feedback.
* Providing a sample txid will expedite a pull request (email support@stake.tax,
  DM @staketax, etc.):

  ```
  # For a given txid, your PR (most commonly) should print different output before/after:
  python3 staketaxcsv/report_osmo.py <wallet_address> --txid <txid>
  ```

# Reference

See [README_reference.md](README_reference.md):

* [Code Style](README_reference.md#code-style)
* [Linting](README_reference.md#linting)
* [Unit Tests](README_reference.md#unit-tests)
* [Docker](README_reference.md#docker)
* [Ideal Configuration](README_reference.md#ideal-configuration)
  * [RPC Node Settings](README_reference.md#rpc-node-settings)
  * [DB Cache](README_reference.md#db-cache)
* [Installing python 3.9.9 on macOS](README_reference.md#installing-python-39-on-macos)
