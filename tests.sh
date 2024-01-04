#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

cur=$(dirname "$(readlink -f "${0}")")

# stop on first error
set -e
#set -v

# pycodestyle
echo "[+] pycodestyle"
pycodestyle --version
pycodestyle catcli/
pycodestyle tests/
pycodestyle setup.py

# pyflakes
echo "[+] pyflakes"
pyflakes --version
pyflakes catcli/
pyflakes tests/
pyflakes setup.py

# pylint
# R0914: Too many local variables
# R0913: Too many arguments
# R0912: Too many branches
# R0915: Too many statements
# R0911: Too many return statements
# R0903: Too few public methods
# R0902: Too many instance attributes
# R0201: no-self-used
echo "[+] pylint"
pylint --version
pylint -sn \
  --disable=R0914 \
  --disable=R0913 \
  --disable=R0912 \
  --disable=R0915 \
  --disable=R0911 \
  --disable=R0903 \
  --disable=R0902 \
  --disable=R0201 \
  --disable=R0022 \
  catcli/

# R0801: Similar lines in 2 files
# W0212: Access to a protected member
# R0914: Too many local variables
# R0915: Too many statements
pylint -sn \
  --disable=R0801 \
  --disable=W0212 \
  --disable=R0914 \
  --disable=R0915 \
  tests/
pylint -sn setup.py

# mypy
echo "[+] mypy"
mypy --strict --disable-error-code=import-untyped catcli/

set +e
grep -R 'TODO' catcli/ && echo "TODO found" && exit 1
grep -R 'FIXME' catcli/ && echo "FIXME found" && exit 1
set -e

# unittest
echo "[+] unittests"
mkdir -p coverages/
coverage run -p --data-file coverages/coverage -m pytest tests

# tests-ng
echo "[+] tests-ng"
for t in "${cur}"/tests-ng/*.sh; do
  echo "running test \"$(basename "${t}")\""
  ${t}
done

# check shells
echo "[+] shellcheck"
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "Install shellcheck"
  exit 1
fi
shellcheck --version
find . -iname '*.sh' | while read -r script; do
  shellcheck -x \
    --exclude SC2002 \
    "${script}"
done

# merge coverage
echo "[+] coverage merge"
coverage combine coverages/*
coverage xml

echo "ALL TESTS DONE OK"
exit 0
