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
ls -laR .github
cat "${catalog}"

#cat "${catalog}"
echo ""

# compare keys
echo "[+] compare keys"
src="tests-ng/assets/github.catalog.json"
src_keys="${tmpd}/src-keys"
dst_keys="${tmpd}/dst-keys"
cat "${src}" | jq '.. | keys?' | jq '.[]' | sort > "${src_keys}"
cat "${catalog}" | jq '.. | keys?' | jq '.[]' | sort > "${dst_keys}"
echo "src:"
cat "${src_keys}"
echo "dst:"
cat "${dst_keys}"
diff "${src_keys}" "${dst_keys}"
echo "ok!"

# compare children 1
echo "[+] compare children 1"
src_keys="${tmpd}/src-child1"
dst_keys="${tmpd}/dst-child1"
cat "${src}" | jq '. | select(.type=="top") | .children | .[].name' | sort > "${src_keys}"
cat "${catalog}" | jq '. | select(.type=="top") | .children | .[].name' | sort > "${dst_keys}"
echo "src:"
cat "${src_keys}"
echo "dst:"
cat "${dst_keys}"
diff "${src_keys}" "${dst_keys}"
echo "ok!"

# compare children 2
echo "[+] compare children 2"
src_keys="${tmpd}/src-child2"
dst_keys="${tmpd}/dst-child2"
cat "${src}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[].name' | sort > "${src_keys}"
cat "${catalog}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[].name' | sort > "${dst_keys}"
echo "src:"
cat "${src_keys}"
echo "dst:"
cat "${dst_keys}"
diff "${src_keys}" "${dst_keys}"
echo "ok!"

# compare children 3
echo "[+] compare children 3"
src_keys="${tmpd}/src-child3"
dst_keys="${tmpd}/dst-child3"
cat "${src}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[] | select(.name=="workflows") | .children | .[].name' | sort > "${src_keys}"
cat "${catalog}" | jq '. | select(.type=="top") | .children | .[] | select(.name=="github") | .children | .[] | select(.name=="workflows") | .children | .[].name' | sort > "${dst_keys}"
echo "src:"
cat "${src_keys}"
echo "dst:"
cat "${dst_keys}"
diff "${src_keys}" "${dst_keys}"
echo "ok!"

# native
echo "[+] compare native output"
native="${tmpd}/native.txt"
${bin} -B ls -s -r --format=native --catalog="${catalog}" > "${native}"
mod="${tmpd}/native.mod.txt"
cat "${native}" | sed -e 's/free:.*%/free:0.0%/g' \
  -e 's/date:....-..-.. ..:..:../date:2023-03-09 16:20:59/g' \
  -e 's#du:[^|]* |#du:0/0 |#g' > "${mod}"
if command -v delta >/dev/null; then
  delta -s "tests-ng/assets/github.catalog.native.txt" "${mod}"
fi
diff --color=always "tests-ng/assets/github.catalog.native.txt" "${mod}"
echo "ok!"

# csv
echo "[+] compare csv output"
csv="${tmpd}/csv.txt"
${bin} -B ls -s -r --format=csv --catalog="${catalog}" > "${csv}"
# modify created csv
mod="${tmpd}/csv.mod.txt"
cat "${csv}" | sed -e 's/"2","[^"]*","[^"]*",""/"2","0","0",""/g' | \
  sed 's/20..-..-.. ..:..:..//g' > "${mod}"
# modify original
ori="${tmpd}/ori.mod.txt"
cat "tests-ng/assets/github.catalog.csv.txt" | \
  sed 's/....-..-.. ..:..:..//g' | \
  sed 's/"2","[^"]*","[^"]*",""/"2","0","0",""/g' > "${ori}"
if command -v delta >/dev/null; then
  delta -s "${ori}" "${mod}"
fi
diff "${ori}" "${mod}"
echo "ok!"

# the end
echo "test \"$(basename "$0")\" success"
cd "${cur}"
exit 0
