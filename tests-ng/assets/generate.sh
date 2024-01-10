#!/usr/bin/env bash
# run me from the root of the package

source tests-ng/helper


rm -f tests-ng/assets/github.catalog.json
python3 -m catcli.catcli index -c github .github --catalog=tests-ng/assets/github.catalog.json

# edit catalog
clean_catalog "tests-ng/assets/github.catalog.json"

# native
python3 -m catcli.catcli ls -r -s -B --catalog=tests-ng/assets/github.catalog.json | \
  sed -e 's/free:.*%/free:0.0%/g' \
  -e 's/....-..-.. ..:..:../2023-03-09 16:20:59/g' \
  -e 's#du:[^|]* |#du:0/0 |#g' > tests-ng/assets/github.catalog.native.txt

# csv
python3 -m catcli.catcli ls -r -s -B --catalog=tests-ng/assets/github.catalog.json --format=csv | \
  sed -e 's/"3","[^"]*","[^"]*",""/"3","0","0",""/g' | \
  sed 's/20..-..-.. ..:..:..//g' > tests-ng/assets/github.catalog.csv.txt