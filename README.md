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
  * Handle archive files (zip, tar, ...) and index their content
  * Save catalog to json for easy versioning with git
  * Command line interface FTW
  * Store files and folders sizes
  * Store md5 hash of files

<a href="https://asciinema.org/a/hRE22qbVtBGxOM1yxw2y4fBy8"><img src="https://asciinema.org/a/hRE22qbVtBGxOM1yxw2y4fBy8.png" width="50%" height="50%"></a>

Quick start:

```bash
# install catcli with pip
sudo pip3 install catcli
# index a directory in the catalog
catcli index -u --meta='some description' log /var/log
# display the content
catcli tree
# navigate
catcli ls log
# find files/folders named '*log*'
catcli find log
```

see [usage](#usage) for specific info

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
  * [Index archive files](#index-archive-files)
  * [Walk indexed files with ls](#walk-indexed-files-with-ls)
  * [Find files](#find-files)
  * [Display entire tree](#display-entire-tree)
  * [Catalog graph](#catalog-graph)
  * [Edit storage](#edit-storage)

* [Examples](#examples)
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
$ virtualenv -p python3 env
$ source env/bin/activate
$ python setup.py install
$ catcli --help
```

# Usage

Each indexed directory is stored in the catalog. Multiple directories can be indexed
and they are all available through the command line interface of catcli.

Five different types of entry are present in a catalog:

  * *top node*: this is the root of the tree
  * *storage node*: this represents some indexed storage (a DVD, an external
    hard drive, an USB drive, some arbitrary directory, ...)
  * *dir node*: this is a directory
  * *file node*: this is a file
  * *archive node*: this is a file contained in an archive

## Index data

Let's say the DVD or external hard drive that needs to be indexed
is mounted on `/media/mnt`. The following command
will index the entire directory `/media/mnt`
and store that in your catalog under the name `<short-name>`.

```bash
$ catcli index --meta=<some-description> -u <short-name> /media/mnt
```

If not specified otherwise (with the switch `--catalog`), the catalog is saved in the current
directory under `catcli.catalog`.

The `--meta` switch allows to add any additional information to store along in
the catalog like for example `the blue disk in my office`.
The `-u` switch tells catcli to also store (and calculate) the total size
of each directory. Using the `-a` switch allows to also index archive files as explained 
[below](#index-archive-files).

## Index archive files

Catcli is able to index and explore the content of archive files.
Following archive formats are supported: tar, tar.gz, tar.xz, lzma, tar.bz2, zip.

Also catcli is able to find files within indexed archive files.

See the [archive example](#archive-example) for more.

## Walk indexed files with ls

A catalog can be walked using the command `ls` as if the media
was mounted.

File/folder separator is `/`
```bash
$ catcli ls tmp/a/b/c
```

Resulting files can be sorted by size using `-S`.

See the [example](#example) for more.

## Find files

Files and directories can be found based on their names
using the `find` command.

See the [example](#example) for more.

## Display entire tree

The entire catalog can be shown using the `tree` command.

Resulting files can be sorted by size using `-S`.

See the [example](#example) for more.

## Catalog graph

The catalog can be exported in a dot file that can be used to
generate a graph of the indexed files.

```bash
$ catcli graph
dot file created under "/tmp/catcli.dot"
create graph with "dot /tmp/catcli.dot -T png -o /tmp/tree.png" (you need graphviz)
$ dot /tmp/catcli.dot -T png -o /tmp/tree.png
```

## Edit storage

Storage entry can be edited with

* `rename` - rename the storage
* `edit` - edit storage metadata

# Examples

## Example
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

Catcli has created its catalog file in the current directory as `catcli.catalog`.

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

When using the `--script` switch, a one-liner is generated
that allows to handle the found file(s)
```bash
$ catcli find 9 --script
test/c/9 [size:0]
op=file; source=/media/mnt; $op ${source}/test/c/9
```

## Archive example

Let's consider a directory containing archive files:
```bash
$ ls -1 /tmp/catcli
catcli-0.3.1
v0.3.1.tar.gz
v0.3.1.zip
```

To enable the indexing of archive contents use
the `-a --archive` switch
```bash
$ catcli index -au some-name /tmp/catcli

Indexed 26 file(s) in 0:00:00.004533
```

Then any command can be used to explore the catalog as for normal
files but, by providing the `-a` switch, archive content are displayed.
```bash
$ catcli ls some-name

   storage: some-name (free:800G, total:1T)
   - catcli-0.3.1 [nbfiles:11, totsize:80.5K]
   - v0.3.1.tar.gz [size:24.2K]
   - v0.3.1.zip [size:31.2K]

$ catcli ls -r some-name/v0.3.1.zip

   v0.3.1.zip [size:31.2K]

$ catcli ls -ar some-name/v0.3.1.zip

   v0.3.1.zip [size:31.2K]
   ├── catcli-0.3.1 [archive:v0.3.1.zip]
   │   ├── catcli [archive:v0.3.1.zip]
   │   │   ├── __init__.py [archive:v0.3.1.zip]
   │   │   ├── catalog.py [archive:v0.3.1.zip]
   │   │   ├── catcli.py [archive:v0.3.1.zip]
   │   │   ├── logger.py [archive:v0.3.1.zip]
   │   │   ├── noder.py [archive:v0.3.1.zip]
   │   │   ├── utils.py [archive:v0.3.1.zip]
   │   │   └── walker.py [archive:v0.3.1.zip]
   │   ├── .gitignore [archive:v0.3.1.zip]
   │   ├── LICENSE [archive:v0.3.1.zip]
   │   ├── MANIFEST.in [archive:v0.3.1.zip]
   │   ├── README.md [archive:v0.3.1.zip]
   │   ├── requirements.txt [archive:v0.3.1.zip]
   │   ├── setup.cfg [archive:v0.3.1.zip]
   │   ├── setup.py [archive:v0.3.1.zip]
   │   ├── tests [archive:v0.3.1.zip]
   │   │   ├── __init__.py [archive:v0.3.1.zip]
   │   │   ├── helpers.py [archive:v0.3.1.zip]
   │   │   ├── test_find.py [archive:v0.3.1.zip]
   │   │   ├── test_graph.py [archive:v0.3.1.zip]
   │   │   ├── test_index.py [archive:v0.3.1.zip]
   │   │   ├── test_ls.py [archive:v0.3.1.zip]
   │   │   ├── test_rm.py [archive:v0.3.1.zip]
   │   │   └── test_tree.py [archive:v0.3.1.zip]
   │   ├── tests.sh [archive:v0.3.1.zip]
   │   └── .travis.yml [archive:v0.3.1.zip]
   └── catcli-0.3.1/ [archive:v0.3.1.zip]
```

All commands can also handle archive file (like `tree` or `find`).

# Contribution

If you are having trouble installing or using catcli, open an issue.

If you want to contribute, feel free to do a PR (please follow PEP8).

The `tests.sh` script can be run to check the code.

# License

This project is licensed under the terms of the GPLv3 license.

