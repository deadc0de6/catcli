#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

cur=$(dirname "$(readlink -f "${0}")")

# stop on first error
set -ev

pycodestyle --version
pycodestyle --ignore=W605 catcli/
pycodestyle tests/

pyflakes --version
pyflakes catcli/
pyflakes tests/

# R0914: Too many local variables
# R0913: Too many arguments
# R0912: Too many branches
# R0915: Too many statements
# R0911: Too many return statements
# R0903: Too few public methods
# R0801: Similar lines in 2 files
# R0902: Too many instance attributes
# R0201: no-self-used
pylint --version
pylint \
  --disable=R0914 \
  --disable=R0913 \
  --disable=R0912 \
  --disable=R0915 \
  --disable=R0911 \
  --disable=R0903 \
  --disable=R0801 \
  --disable=R0902 \
  --disable=R0201 \
  --disable=R0022 \
  catcli/
pylint \
  --disable=W0212 \
  --disable=R0914 \
  --disable=R0915 \
  --disable=R0801 \
  tests/

mypy \
  --strict \
  catcli/

nosebin="nose2"
PYTHONPATH=catcli ${nosebin} --with-coverage --coverage=catcli

for t in ${cur}/tests-ng/*; do
  echo "running test \"`basename ${t}`\""
  ${t}
done

exit 0
