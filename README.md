
# staketaxcsv

  * Python repo to create blockchain CSVs for Terra (LUNA), Solana (SOL), and Cosmos (ATOM).
  * CSV codebase for stake.tax
  * Community contribution and PRs are most welcome, especially to fix/support new types of 
    protocols/transactions.


# Install

  1. Install python 3.9.9 ([one way](README_reference.md#installing-python-39-on-macos))
  2. Install pip packages ```pip3 install -r requirements.txt```
  3. Edit (~/.bashrc, ~/.zshrc, shell equivalent) so that it loads `sample.env` in shell:
  ```
  set -o allexport
  source <PATH_TO_SAMPLE_ENV_HERE>/sample.env
  set +o allexport
   ```
    
  4. For ATOM only, install `gaiad` 
  - https://hub.cosmos.network/main/gaia-tutorials/installation.html

# Usage

  * Same arguments apply for report_terra.py (LUNA), report_sol.py (SOL), report_atom.py (ATOM):
    ```
    cd src
    
    # Create default CSV
    python3 report_terra.py <wallet_address>
    
    # Create all CSV formats (i.e. koinly, cointracking, etc.)
    python3 report_terra.py <wallet_address> --format all
    
    # Show CSV result for single transaction (great for development/debugging)
    python3 report_terra.py <wallet_address> --txid <txid>
    ```

# Contributing Code

  * Code style follows `pep8`.  This can be tested with `pycodestyle`.
  * Providing a sample transaction txid (email support@stake.tax, DM @staketax, etc.)
    is the fastest way for changes to be included:
    ```
    # For a given txid, your PR (most commonly) should print different output before/after:
    python3 report_terra.py <wallet_address> --txid <txid>
    ```

# Reference

  * See [README_reference.md](README_reference.md) for more notes:
    * [Ideal Configuration](README_reference.md#ideal-configuration)
      * [RPC Node Settings](README_reference.md#rpc-node-settings)
      * [DB Cache](README_reference.md#db-cache)
    * [Installing python 3.9.9 on MacOS](README_reference.md#installing-python-39-on-macos)
    * [Unit Tests](README_reference.md#unit-tests)
