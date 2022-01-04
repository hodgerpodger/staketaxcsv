#!/bin/sh
set -euo pipefail

# change to current directory
cd "$(dirname "$(readlink -f "${0}")")"

# check chain / help
chain="${1:-"help"}"
if [ "${chain}" = "help" ] || [ "${1#-}" != "$1" ]; then
  echo
  echo '👷 I can offer you the following chains:'
  ls -1 ./src/report_*.py | sed -nE 's/.+_(\w+).+/- \1/p'
  echo
  echo '👣 Than execute: ... <chain> <wallet address> [optional commands see -h]'
  echo

  exit 0
fi

# check if main scripts should be executed
script="./src/report_${1}.py"
if [ -f "${script}" ]; then
  shift
  set -- python3 "${script}" "${@}"
fi

# shortcut for docker volume binding
[ ! -d /reports ] || [ -L src/_reports ] || {
  rm -r src/_reports
  ln -s /reports src/_reports
}

exec "${@}"