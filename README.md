# CATCLI

[![Build Status](https://travis-ci.org/deadc0de6/catcli.svg?branch=master)](https://travis-ci.org/deadc0de6/catcli)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Coverage Status](https://coveralls.io/repos/github/deadc0de6/catcli/badge.svg?branch=master)](https://coveralls.io/github/deadc0de6/catcli?branch=master)
[![PyPI version](https://badge.fury.io/py/catcli.svg)](https://badge.fury.io/py/catcli)
[![Python](https://img.shields.io/pypi/pyversions/catcli.svg)](https://pypi.python.org/pypi/catcli)

*The command line catalog tool for your offline data*

Did you ever wanted to find back that specific file that should be on one of your
backup DVDs or one of your external hard drives ? You usually go through all
of them hoping to find the right one on the first try ?
Well [catcli](https://github.com/deadc0de6/catcli) indexes external media
in a catalog and allows to quickly find specific files or even navigate in the
catalog of indexed files while these are not connected to your host.

Features:

  * Index any directories in a catalog
  * Ability to search for files by name in the catalog
  * Ability to navigate through indexed data à la `ls`
  * Save catalog to json for easy versioning with git
  * Command line interface FTW
  * Store files and folders sizes
  * Store md5 hash of files

Quick start:

```bash
# index a directory in the catalog
catcli index -u --meta='some description' log /var/log
# display the content
catcli tree
# navigate
catcli ls log
# find files/folders named '*log*'
catcli find log
```

see [usage](#usage) for specific info.

## Why catcli ?

[Catcli](https://github.com/deadc0de6/catcli) gives the ability to navigate,
explore and find your files that are stored on external media
(DVDs, hard drives, USB sticks, etc) when those are not connected.
Catcli can just as easily index any arbitrary directories.

See the [example](#example) for an overview of the available features.

---

**Table of Contents**

* [Installation](#installation)
* [Usage](#usage)

  * [Index data](#index-data)
  * [Walk indexed files with ls](#walk-indexed-files-with-ls)
  * [Find files](#find-files)
  * [Display entire tree](#display-entire-tree)

* [Example](#example)
* [Contribution](#contribution)

# Installation

To install run:
```bash
$ sudo pip3 install catcli
```

Or from github directly
```bash
$ cd /tmp; git clone https://github.com/deadc0de6/catcli && cd catcli
$ sudo python3 setup.py install
$ catcli --help
```

To work with catcli without installing it, you can do the following
```bash
$ cd /tmp; git clone https://github.com/deadc0de6/catcli && cd catcli
$ sudo pip3 install -r requirements.txt
$ python3 -m catcli.catcli --help
```

or install it in a virtualenv
```bash
$ cd /tmp; git clone https://github.com/deadc0de6/catcli && cd catcli
$ virtualenv env
$ source env/bin/activate
$ python setup.py install
$ catcli --help
```

# Usage

Each indexed directory is stored in the catalog. Multiple directories can be indexed
and they are all available through the command line interface of catcli.

Four different types of entry are present in a catalog:

  * *top node*: this is the root of the tree
  * *storage node*: this represents some indexed storage (a DVD, an external
    hard drive, an USB drive, some arbitrary directory, ...)
  * *dir node*: this is a directory
  * *file node*: this is a file

## Index data

Let's say the DVD or external hard drive that needs to be indexed
is mounted on `/media/mnt`. The following command
will index the entire directory `/media/mnt`
and store that in your catalog under the name `<short-name>`.

```bash
$ catcli index --meta=<some-description> -u <short-name> /media/mnt
```

If not specified otherwise (switch `--catalog`), the catalog is saved in the current
directory under `catcli.catalog`.

The `--meta` switch allows to add any additional information to store along in
the catalog like for example `the blue disk in my office`.
The `-u` switch tells catcli to also store (and calculate) the total size
of each directory.

## Walk indexed files with ls

A catalog can be walked using the command `ls` as if the media
was mounted.

File/folder separator is `/`
```bash
$ catcli ls tmp/a/b/c
```

See the [example](#example) for more.

## Find files

Files and directories can be found based on their names
using the `find` command.

See the [example](#example) for more.

## Display entire tree

The entire catalog can be shown using the `tree` command.

See the [example](#example) for more.

# Example

Let's first create some files and directories:
```bash
$ mkdir -p /tmp/test/{a,b,c}
$ touch /tmp/test/a/{1,2,3}
$ touch /tmp/test/b/{4,5,6}
$ touch /tmp/test/c/{7,8,9}
$ ls -R /tmp/test
/tmp/test:
a  b  c

/tmp/test/a:
1  2  3

/tmp/test/b:
4  5  6

/tmp/test/c:
7  8  9
```

First this directory is indexed by catcli as if it was some kind of
external storage:
```bash
$ catcli index --meta='my test directory' -u tmptest /tmp/test
```

Catcli has created its catalog in the current directory as `catcli.catalog`.

Printing the entire catalog as a tree is done with the command `tree`
```
$ catcli tree
top
└── storage: tmptest (free:183.7G, total:200.0G) (my test directory)
    ├── b [nbfiles:3]
    │   ├── 4 [size:0]
    │   ├── 5 [size:0]
    │   └── 6 [size:0]
    ├── a [nbfiles:3]
    │   ├── 1 [size:0]
    │   ├── 3 [size:0]
    │   └── 2 [size:0]
    └── c [nbfiles:3]
        ├── 7 [size:0]
        ├── 8 [size:0]
        └── 9 [size:0]
```

The catalog can be walked with `ls` as if it was a normal directory
```
$ catcli ls
top
- storage: tmptest (free:2.6G, total:2.6G) (my test directory)

$ catcli ls tmptest
storage: tmptest (free:3.7G, total:3.7G) (my test directory)
- a [nbfiles:3]
- b [nbfiles:3]
- c [nbfiles:3]

$ catcli ls tmptest/b
b [nbfiles:3]
- 4 [size:0]
- 5 [size:0]
- 6 [size:0]
```

And files can be found using the command `find`
```bash
$ catcli find 9
test/c/9 [size:0]
```

When using the `-s` switch, a one-liner is generated
that allows to handle the found file(s)
```bash
$ catcli find 9 -s
test/c/9 [size:0]
op=file; source=/media/mnt; $op ${source}/test/c/9
```

# Contribution

If you are having trouble installing or using catcli, open an issue.

If you want to contribute, feel free to do a PR (please follow PEP8).

The `tests.sh` script can be run to check the code.

# License

This project is licensed under the terms of the GPLv3 license.

