#!/bin/sh
set -euo pipefail

# change to current directory
cd "$(dirname "$(readlink -f "${0}")")"

script="./src/report_${1:?"Missing chain! E.g. terra"}.py"
if [ ! -f "${script}" ]; then
  {
    echo "No report for chain ${1}." 
    ls -1 ./src/report_*.py | sed -nE 's/.+_(\w+).+/\1/p'
  } > /dev/stderr
  exit 1
fi
shift

# shortcut for docker volume binding
[ ! -d /reports ] || [ -L src/_reports ] || {
  rm -r src/_reports
  ln -s /reports src/_reports
}

exec python3 "${script}" "${@}"