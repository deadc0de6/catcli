#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# exit on first error
set -e

# get current path
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found !" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

# pivot
prev="${cur}/.."
cd "${prev}"

# coverage
#export PYTHONPATH=".:${PYTHONPATH}"
bin="python3 -m catcli.catcli"
if hash coverage 2>/dev/null; then
  bin="coverage run -p --source=catcli -m catcli.catcli"
  #bin="coverage run -p --source=${prev}/catcli -m catcli.catcli"
fi

echo "current dir: $(pwd)"
echo "pythonpath: ${PYTHONPATH}"
echo "bin: ${bin}"
${bin} --version

# get the helpers
# shellcheck source=tests-ng/helper
source "${cur}"/helper
echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"

##########################################################
# the test
##########################################################

# create temp dirs
tmpd=$(mktemp -d)
clear_on_exit "${tmpd}"

catalog="${tmpd}/catalog"

# index
${bin} -B index -c --catalog="${catalog}" github .github
cat "${catalog}"

# make sure we still get the same output in native format
native="${tmpd}/native.txt"
${bin} -B ls -r -s --format=native --catalog="${catalog}" > "${native}"
diff -I '^.*| totsize.*$' "${cur}/assets/github.catalog.native.txt" "${native}"

# make sure we still get the same output in csv
csv="${tmpd}/csv.txt"
${bin} -B ls -r -s --format=csv --catalog="${catalog}" > "${csv}"
diff -I '^.*| totsize.*$' "${cur}/assets/github.catalog.csv.txt" "${csv}"

# the end
echo "test \"$(basename "$0")\" success"
cd "${cur}"
exit 0
