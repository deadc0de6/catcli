# CATCLI

[![Tests Status](https://github.com/deadc0de6/catcli/workflows/tests/badge.svg?branch=master)](https://github.com/deadc0de6/catcli/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Coveralls](https://img.shields.io/coveralls/github/deadc0de6/catcli)](https://coveralls.io/github/deadc0de6/catcli?branch=master)

[![PyPI version](https://badge.fury.io/py/catcli.svg)](https://badge.fury.io/py/catcli)
[![AUR](https://img.shields.io/aur/version/catcli-git.svg)](https://aur.archlinux.org/packages/catcli-git)
[![Python](https://img.shields.io/pypi/pyversions/catcli.svg)](https://pypi.python.org/pypi/catcli)

[![Donate](https://img.shields.io/badge/donate-KoFi-blue.svg)](https://ko-fi.com/deadc0de6)

*The command line catalog tool for your offline data*

Did you ever wanted to find back that specific file that should be on one of your
backup DVDs or one of your external hard drives? You usually go through all
of them hoping to find the right one on the first try?
[Catcli](https://github.com/deadc0de6/catcli) indexes external media
in a catalog file and allows to quickly find specific files or even navigate in the
catalog of indexed files while these are not connected to your host.

Features:

  * Index any directories in a catalog
  * Ability to search for files by name in the catalog
  * Ability to navigate through indexed data à la `ls`
  * Support for fuse to mount the indexed data as a virtual filesystem
  * Handle archive files (zip, tar, ...) and index their content
  * Save catalog to json for easy versioning with git
  * Command line interface FTW
  * Store files and directories sizes
  * Store md5 hash of files
  * Ability to update the catalog
  * Support for `fzf` for finding files
  * Tag your different storages with additional information
  * Export catalog to CSV

<a href="https://asciinema.org/a/hRE22qbVtBGxOM1yxw2y4fBy8"><img src="https://asciinema.org/a/hRE22qbVtBGxOM1yxw2y4fBy8.png" width="50%" height="50%"></a>

Quick start:

```bash
# install catcli with pip
pip3 install catcli --user
# index a directory in the catalog
catcli index --meta='some description' log /var/log
# display the content
catcli ls -r
# navigate
catcli ls log
# find files/directories named '*log*'
catcli find log
```

see [usage](#usage) for specific info

## Why catcli?

[Catcli](https://github.com/deadc0de6/catcli) gives the ability to navigate,
explore and find your files that are stored on external media
(DVDs, hard drives, USB sticks, etc) when those are not connected.
Catcli can just as easily index any arbitrary directories.

See the [examples](#examples) for an overview of the available features.

---

**Table of Contents**

* [Installation](#installation)
* [Usage](#usage)

  * [Index data](#index-data)
  * [Index archive files](#index-archive-files)
  * [Walk indexed files with ls](#walk-indexed-files-with-ls)
  * [Find files](#find-files)
  * [Mount catalog](#mount-catalog)
  * [Display entire hierarchy](#display-entire-hierarchy)
  * [Catalog graph](#catalog-graph)
  * [Edit storage](#edit-storage)
  * [Update catalog](#update-catalog)
  * [CSV format](#csv-format)

* [Examples](#examples)
* [Contribution](#contribution)
* [Thank you](#thank-you)

# Installation

Install from Pypi
```bash
$ pip3 install catcli --user
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
$ pip3 install -r requirements.txt --user
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

Catcli is also available on aur: https://aur.archlinux.org/packages/catcli-git/

# Usage

Each indexed directory is stored in the catalog. Multiple directories can be indexed
and they are all available through the command line interface of catcli.

Five different types of entry are present in a catalog:

  * **top node**: this is the root of the hierarchy
  * **storage node**: this represents an indexed storage (a DVD, an external
    hard drive, an USB drive, some arbitrary directory, etc).
  * **dir node**: this is a directory
  * **file node**: this is a file
  * **archive node**: this is a file contained in an archive (tar, zip, etc)

## Index data

Let's say the DVD or external hard drive that needs to be indexed
is mounted on `/media/mnt`. The following command
will index the entire directory `/media/mnt`
and store that in your catalog under the name `<short-name>`.

```bash
$ catcli index --meta=<some-description> <short-name> /media/mnt
```

If not specified otherwise (with the switch `--catalog`), the catalog is saved in the current
directory under `catcli.catalog`.

The `--meta` switch allows to add any additional information to store along in
the catalog like for example `the blue disk in my office`.

Catcli will calculate and store the total size of each node (directories, storages, etc)
unless the `-n --no-subsize` switch is used.

Using the `-a --archive` switch allows to also index archive files as explained
[below](#index-archive-files).

## Index archive files

Catcli is able to index and explore the content of archive files.
Following archive formats are supported: *tar*, *tar.gz*, *tar.xz*, *lzma*, *tar.bz2*, *zip*.
Catcli is also able to find files within indexed archive files.

See the [archive example](#archive-example) for more.

## Walk indexed files with ls

A catalog can be walked using the command `ls` as if the media
is mounted (File/directories separator is `/`).

```bash
$ catcli ls tmp/a/b/c
```

Resulting files can be sorted by size using `-S --sortsize`.
See the [examples](#examples) for more.

## Find files

Files and directories can be found based on their names
using the `find` command.

`Find` support two formats that allow to use `fzf` for
searching:

* `--format=fzf-native`: display the result in native format
* `--format=fzf-csv`: display the result in csv

See the [examples](#examples) for more.

## Mount catalog

The catalog can be mounted with [fuse](https://www.kernel.org/doc/html/next/filesystems/fuse.html)
and navigate like any filesystem.

```bash
$ mkdir /tmp/mnt
$ catcli index -c github .github
$ catcli mount /tmp/mnt
$ ls -laR /tmp/mnt
drwxrwxrwx - user  8 Mar 22:08 github

mnt/github:
.rwxrwxrwx 17 user 19 Oct  2022 FUNDING.yml
drwxrwxrwx  - user  2 Mar 10:15 workflows

mnt/github/workflows:
.rwxrwxrwx 691 user 19 Oct  2022 pypi-release.yml
.rwxrwxrwx 635 user  8 Mar 21:08 testing.yml
```

## Display entire hierarchy

The entire catalog can be shown using the `ls -r` command.
Resulting files can be sorted by size using the `-S --sortsize` switch.

See the [examples](#examples) for more.

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

Storage entry can be edited with following catcli commands:

* `rename` - rename the storage
* `edit` - edit storage metadata

## Update catalog

The catalog can be updated with the `update` command.
Updates are based on the access time of each of the files and on the
hash checksum if present (catalog was indexed with `-c --hash` and
`update` is called with the switch `-c --hash`).

## CSV format

Results can be printed to CSV using `--format=csv`.
Fields are separated by a comma (`,`) and are quoted with double quotes (`"`).

Each line contains the following fields:

* **name**: the entry name
* **type**: the entry type (file, directory, storage, etc)
* **path**: the entry path
* **size**: the entry size
* **indexed_at**: when this entry was indexed
* **maccess**: the entry modification date/time
* **md5**: the entry checksum (if any)
* **nbfiles**: the number of children (empty for nodes that are not storage or directory)
* **free_space**: free space (empty for not storage nodes)
* **total_space**: total space (empty for not storage nodes)
* **meta**: meta information (empty for not storage nodes)

# Examples

## Simple example

Let's first create some files and directories:

```bash
$ mkdir -p /tmp/test/{a,b,c}
$ echo 'something in files in a' > /tmp/test/a/{1,2,3}
$ echo 'something else in files in b' > /tmp/test/b/{4,5,6}
$ echo 'some bytes' > /tmp/test/c/{7,8,9}
$ tree /tmp/test
/tmp/test
├── a
│   ├── 1
│   ├── 2
│   └── 3
├── b
│   ├── 4
│   ├── 5
│   └── 6
└── c
    ├── 7
    ├── 8
    └── 9

3 directories, 9 files
```

First this directory is indexed with `catcli` as if it was some kind of
external storage:

```bash
$ catcli index --meta='my test directory' tmptest /tmp/test
```

Catcli creates its catalog file in the current directory as `catcli.catalog`.

Printing the entire catalog as a tree is done with the command `ls -r`

```
$ catcli ls -r
top
└── storage: tmptest (my test directory) (nbfiles:3, free:3.7G/3.7G, date:2019-01-26 19:59:47)
    ├── a [nbfiles:3, totsize:72]
    │   ├── 1 [size:24]
    │   ├── 2 [size:24]
    │   └── 3 [size:24]
    ├── b [nbfiles:3, totsize:87]
    │   ├── 4 [size:29]
    │   ├── 5 [size:29]
    │   └── 6 [size:29]
    └── c [nbfiles:3, totsize:33]
        ├── 7 [size:11]
        ├── 8 [size:11]
        └── 9 [size:11]
```

The catalog can be walked with `ls` as if it was a normal directory

```
$ catcli ls
top
- storage: tmptest (my test directory) (nbfiles:3, free:3.7G/3.7G, date:2019-01-26 19:59:47)

$ catcli ls tmptest
storage: tmptest (my test directory) (nbfiles:3, free:3.7G/3.7G, date:2019-01-26 19:59:47)
- a [nbfiles:3, totsize:72]
- b [nbfiles:3, totsize:87]
- c [nbfiles:3, totsize:33]

$ catcli ls tmptest/b
b [nbfiles:3, totsize:87]
- 4 [size:29]
- 5 [size:29]
- 6 [size:29]
```

And files can be found using the command `find`

```bash
$ catcli find 9

c/9 [size:11, storage:tmptest]
```

When using the `-b --script` switch, a one-liner is generated
that allows to handle the found file(s)

```
$ catcli find 9 --script

c/9 [size:11, storage:tmptest]
op=file; source=/media/mnt; $op ${source}/c/9
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
```

Then any command can be used to explore the catalog as for normal
files but, by providing the `-a --archive` switch, archive content are displayed.

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

# Contribution

If you are having trouble installing or using catcli, open an issue.

If you want to contribute, feel free to do a PR (please follow PEP8).

The `tests.sh` script can be run to check the code.

# Thank you

If you like catcli, [buy me a coffee](https://ko-fi.com/deadc0de6).

# License

This project is licensed under the terms of the GPLv3 license.

