#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6

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
tmpu="${tmpd}/dir2"
mkdir -p "${tmpu}"

catalog="${tmpd}/catalog"

mkdir -p "${tmpd}/dir"
echo "abc" > "${tmpd}/dir/a"

# index
${bin} -B index --catalog="${catalog}" dir "${tmpd}/dir"
${bin} -B ls --catalog="${catalog}" dir

# get attributes
freeb=$(${bin} -B ls --catalog="${catalog}" dir | grep free: | sed 's/^.*,free:\([^ ]*\).*$/\1/g')
dub=$(${bin} -B ls --catalog="${catalog}" dir | grep du: | sed 's/^.*,du:\([^ ]*\).*$/\1/g')
dateb=$(${bin} -B ls --catalog="${catalog}" dir | grep date: | sed 's/^.*,date: \(.*\)$/\1/g')
echo "before: free:${freeb} | du:${dub} | date:${dateb}"

# change content
echo "abc" >> "${tmpd}/dir/a"
echo "abc" > "${tmpd}/dir/b"

# move dir
cp -r "${tmpd}/dir" "${tmpu}/"

# sleep to force date change
sleep 1

# update
${bin} -B update -f --catalog="${catalog}" dir "${tmpu}/dir"
${bin} -B ls --catalog="${catalog}" dir

# get new attributes
freea=$(${bin} -B ls --catalog="${catalog}" dir | grep free: | sed 's/^.*,free:\([^ ]*\).*$/\1/g')
dua=$(${bin} -B ls --catalog="${catalog}" dir | grep du: | sed 's/^.*,du:\([^ ]*\).*$/\1/g')
datea=$(${bin} -B ls --catalog="${catalog}" dir | grep date: | sed 's/^.*,date: \(.*\)$/\1/g')
echo "after: free:${freea} | du:${dua} | date:${datea}"

# test they are all different
[ "${freeb}" = "${freea}" ] && echo "WARNING free didn't change!"
[ "${dub}" = "${dua}" ] && echo "WARNING du didn't change!"
[ "${dateb}" = "${datea}" ] && echo "WARNING date didn't change!" && exit 1

# the end
echo "test \"$(basename "$0")\" success"
cd "${cur}"
exit 0
