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

# R0914: Too many local variables
# R0913: Too many arguments
# R0912: Too many branches
# R0915: Too many statements
# R0911: Too many return statements
pylint \
  --disable=R0914 \
  --disable=R0913 \
  --disable=R0912 \
  --disable=R0915 \
  --disable=R0911 \
  catcli/
pylint \
  --disable=W0212 \
  --disable=R0914 \
  --disable=R0915 \
  --disable=R0801 \
  tests/

nosebin="nose2"
PYTHONPATH=catcli ${nosebin} --with-coverage --coverage=catcli

for t in ${cur}/tests-ng/*; do
  echo "running test \"`basename ${t}`\""
  ${t}
done

exit 0
