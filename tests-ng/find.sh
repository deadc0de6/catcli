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
  bin="coverage run -p --source=catcli -m catcli.catcli"
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

#cat "${catalog}"
echo ""

${bin} -B find --catalog="${catalog}" testing.yml
cnt=$(${bin} -B find --catalog="${catalog}" testing.yml | wc -l)
[ "${cnt}" != "2" ] && echo "should return 2!" && exit 1

# the end
echo ""
echo "test \"$(basename "$0")\" success"
cd "${cur}"
exit 0
