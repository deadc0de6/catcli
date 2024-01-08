#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2024, deadc0de6

set -e
cur=$(cd "$(dirname "${0}")" && pwd)
prev="${cur}/.."
cd "${prev}"

# coverage
bin="python3 -m catcli.catcli"
if command -v coverage 2>/dev/null; then
  mkdir -p coverages/
  bin="coverage run -p --data-file coverages/coverage --source=catcli -m catcli.catcli"
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
${bin} -B index -c -f --catalog="${catalog}" github1 .github
${bin} -B index -c -f --catalog="${catalog}" github2 .github
clean_catalog "${catalog}"

#cat "${catalog}"
echo ""

${bin} -B ls -r --catalog="${catalog}"

${bin} -B ls --catalog="${catalog}" 'github1/*.yml'
cnt=$(${bin} -B ls --catalog="${catalog}" 'github1/*.yml' | wc -l)
[ "${cnt}" != "2" ] && echo "should return 2 (not ${cnt})" && exit 1

${bin} -B ls --catalog="${catalog}" 'github*/*.yml'
cnt=$(${bin} -B ls --catalog="${catalog}" 'github*/*.yml' | wc -l)
[ "${cnt}" != "4" ] && echo "should return 4 (not ${cnt})" && exit 1

# the end
echo ""
echo "test \"$(basename "$0")\" success"
cd "${cur}"
exit 0
