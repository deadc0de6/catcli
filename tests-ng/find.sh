#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

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

echo "finding \"testing.yml\""
${bin} -B find --catalog="${catalog}" testing.yml
cnt=$(${bin} -B find --catalog="${catalog}" testing.yml | wc -l)
[ "${cnt}" != "2" ] && echo "should return 2 (not ${cnt})" && exit 1

echo "finding \"*.yml\""
${bin} -B find --catalog="${catalog}" '*.yml'
cnt=$(${bin} -B find --catalog="${catalog}" '*.yml' | wc -l)
[ "${cnt}" != "8" ] && echo "should return 8 (not ${cnt})" && exit 1

# the end
echo ""
echo "test \"$(basename "$0")\" success"
cd "${cur}"
exit 0
