#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# exit on first error
set -e

# get current path
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! command -v ${rl}; then
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
if command -v coverage 2>/dev/null; then
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
echo ""

# compare keys
src="tests-ng/assets/github.catalog.json"
src_keys="${tmpd}/src-keys"
dst_keys="${tmpd}/dst-keys"
cat "${src}" | jq '.. | keys?' | jq '.[]' > "${src_keys}"
cat "${catalog}" | jq '.. | keys?' | jq '.[]' > "${dst_keys}"
diff "${src_keys}" "${dst_keys}"

# compare children 1
src_keys="${tmpd}/src-child1"
dst_keys="${tmpd}/dst-child1"
cat "${src}" | jq '. | select(.type=="top") | .children | .[].name' > "${src_keys}"
cat "${catalog}" | jq '. | select(.type=="top") | .children | .[].name' > "${dst_keys}"
diff "${src_keys}" "${dst_keys}"

# compare children 2
src_keys="${tmpd}/src-child2"
dst_keys="${tmpd}/dst-child2"
cat "${src}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[].name' > "${src_keys}"
cat "${catalog}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[].name' > "${dst_keys}"
diff "${src_keys}" "${dst_keys}"

# compare children 3
src_keys="${tmpd}/src-child3"
dst_keys="${tmpd}/dst-child3"
cat "${src}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[] | select(.name=="workflows") | .children | .[].name' > "${src_keys}"
cat "${catalog}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[] | select(.name=="workflows") | .children | .[].name' > "${dst_keys}"
diff "${src_keys}" "${dst_keys}"

# native
native="${tmpd}/native.txt"
${bin} -B ls -s -r --format=native --catalog="${catalog}" > "${native}"
mod="${tmpd}/native.mod.txt"
cat "${native}" | sed -e 's/free:.*%/free:0.0%/g' \
  -e 's/date:.*$/date:2023-03-09 16:20:59/g' \
  -e 's#du:[^|]* |#du:0/0 |#g' > "${mod}"
#delta "tests-ng/assets/github.catalog.native.txt" "${mod}"
diff --color=always "tests-ng/assets/github.catalog.native.txt" "${mod}"

# csv
csv="${tmpd}/csv.txt"
${bin} -B ls -s -r --format=csv --catalog="${catalog}" > "${csv}"
mod="${tmpd}/csv.mod.txt"
cat "${csv}" | sed -e 's/"2",".*",".*",""$/"2","0","0",""/g' | \
  sed 's/20..-..-.. ..:..:..//g' > "${mod}"
ori="${tmpd}/ori.mod.txt"
cat "tests-ng/assets/github.catalog.csv.txt" | \
  sed 's/20..-..-.. ..:..:..//g' > "${ori}"
#delta "${ori}" "${mod}"
diff "${ori}" "${mod}"

# the end
echo "test \"$(basename "$0")\" success"
cd "${cur}"
exit 0
