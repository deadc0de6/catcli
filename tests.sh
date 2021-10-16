#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

cur=$(dirname "$(readlink -f "${0}")")

# stop on first error
set -ev

pycodestyle --ignore=W605 catcli/
pycodestyle tests/

pyflakes catcli/
pyflakes tests/

PYTHONPATH=catcli python3 -m nose -s --with-coverage --cover-package=catcli
#PYTHONPATH=catcli python3 -m nose -s

for t in ${cur}/tests-ng/*; do
  echo "running test \"`basename ${t}`\""
  ${t}
done

exit 0
