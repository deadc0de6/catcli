#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6

cur=$(dirname "$(readlink -f "${0}")")
cwd=`pwd`

# pivot
cd ${cur}/../
python3 -m catcli.catcli --version

##########################################################
# the test
##########################################################

# create temp dirs
tmpd=`mktemp -d`
tmpu="${tmpd}/dir2"
mkdir -p ${tmpu}

# setup cleaning
clean() {
  # clean
  rm -rf ${tmpd} ${tmpu}
}
trap clean EXIT

catalog="${tmpd}/catalog"

mkdir -p ${tmpd}/dir
echo "abc" > ${tmpd}/dir/a

# index
python3 -m catcli.catcli -B index --catalog=${catalog} dir ${tmpd}/dir
python3 -m catcli.catcli -B ls --catalog=${catalog} dir

# get attributes
freeb=`python3 -m catcli.catcli -B ls --catalog=${catalog} dir | grep free: | sed 's/^.*,free:\([^ ]*\).*$/\1/g'`
dub=`python3 -m catcli.catcli -B ls --catalog=${catalog} dir | grep du: | sed 's/^.*,du:\([^ ]*\).*$/\1/g'`
dateb=`python3 -m catcli.catcli -B ls --catalog=${catalog} dir | grep date: | sed 's/^.*,date: \(.*\)$/\1/g'`
echo "before: free:${freeb} | du:${dub} | date:${dateb}"

# change content
echo "abc" >> ${tmpd}/dir/a
echo "abc" > ${tmpd}/dir/b

# move dir
cp -r ${tmpd}/dir ${tmpu}/

# sleep to force date change
sleep 1

# update
python3 -m catcli.catcli -B update -f --catalog=${catalog} dir ${tmpu}/dir
python3 -m catcli.catcli -B ls --catalog=${catalog} dir

# get new attributes
freea=`python3 -m catcli.catcli -B ls --catalog=${catalog} dir | grep free: | sed 's/^.*,free:\([^ ]*\).*$/\1/g'`
dua=`python3 -m catcli.catcli -B ls --catalog=${catalog} dir | grep du: | sed 's/^.*,du:\([^ ]*\).*$/\1/g'`
datea=`python3 -m catcli.catcli -B ls --catalog=${catalog} dir | grep date: | sed 's/^.*,date: \(.*\)$/\1/g'`
echo "after: free:${freea} | du:${dua} | date:${datea}"

# test they are all different
[ "${freeb}" = "${freea}" ] && echo "WARNING free didn't change!"
[ "${dub}" = "${dua}" ] && echo "WARNING du didn't change!"
[ "${dateb}" = "${datea}" ] && echo "date didn't change!" && exit 1

# pivot back
cd ${cwd}

# the end
echo "test \"`basename $0`\" success"
exit 0
