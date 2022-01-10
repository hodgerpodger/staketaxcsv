
# staketaxcsv

* Python repository to create blockchain CSVs for Terra (LUNA), Solana (SOL), Cosmos (ATOM),
  and Osmosis (OSMO) blockchains.
* CSV codebase for <https://stake.tax>
* Community contribution and PRs are most welcome, especially to fix/support new types of
  protocols/transactions.

# Usage

* Same arguments apply for report_terra.py (LUNA), report_sol.py (SOL), report_atom.py (ATOM),
  report_osmo.py (OSMO):
  ```sh
  # Load environment variables from sample.env (add to ~/.bash_profile or ~/.bashrc to avoid doing every time)
  set -o allexport
  source sample.env
  set +o allexport
  
  cd src
  
  # Create default CSV
  python3 report_terra.py <wallet_address>
  
  # Create all CSV formats (i.e. koinly, cointracking, etc.)
  python3 report_terra.py <wallet_address> --format all
  
  # Show CSV result for single transaction (great for development/debugging)
  python3 report_terra.py <wallet_address> --txid <txid>
  ```

# Install

1. Install python 3.9 ([one way](README_reference.md#installing-python-39-on-macos))
2. Install pip packages
   ```sh
   pip3 install -r requirements.txt
   ```

# Docker

See [Docker](README_reference.md#docker) to alternatively install/run in docker container.


# Contributing Code

* Code style follows `pep8`.  This can be tested with `pycodestyle`.
* Providing a sample txid will expedite a pull request (email support@stake.tax,
  DM @staketax, etc.):
  ```sh
  # For a given txid, your PR (most commonly) should print different output before/after:
  python3 report_terra.py <wallet_address> --txid <txid>
  ```

# Reference

See [README_reference.md](README_reference.md):

* [Code Style](README_reference.md#code-style)
* [Unit Tests](README_reference.md#unit-tests)
* [Docker](README_reference.md#docker)
* [Ideal Configuration](README_reference.md#ideal-configuration)
  * [RPC node.js Settings](README_reference.md#rpc-node-settings)
  * [DB Cache](README_reference.md#db-cache)
* [Installing python 3.9.9 on macOS](README_reference.md#installing-python-39-on-macos)
