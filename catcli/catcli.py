#!/usr/bin/env python3
# author: deadc0de6

"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Catcli command line interface
"""

import sys
import os
import datetime
from docopt import docopt

# local imports
from . import __version__ as VERSION
from .logger import Logger
from .catalog import Catalog
from .walker import Walker
from .noder import Noder

NAME = 'catcli'
CUR = os.path.dirname(os.path.abspath(__file__))
CATALOGPATH = NAME+'.catalog'
GRAPHPATH = '/tmp/'+NAME+'.dot'
SEPARATOR = '/'
WILD = '*'

BANNER = """ +-+-+-+-+-+-+
 |c|a|t|c|l|i|
 +-+-+-+-+-+-+ v{}""".format(VERSION)

USAGE = """
{0}

Usage:
    {1} index [--catalog=<path>] [--meta=<meta>...] [-fcuV] <name> <path>
    {1} ls    [--catalog=<path>] [-rV] [<path>]
    {1} find  [--catalog=<path>] [-sV] <term>
    {1} rm    [--catalog=<path>] [-fV] <storage>
    {1} tree  [--catalog=<path>] [-V] [<path>]
    {1} graph [--catalog=<path>] [-V] [<path>]
    {1} help
    {1} --help
    {1} --version

Options:
    --catalog=<path>    Path to the catalog [default: {2}].
    --meta=<meta>       Additional attribute to store [default: ].
    -u --subsize        Store size of folders [default: False].
    -f --force          Force overwrite [default: False].
    -s --script         Output script to manage found file(s) [default: False].
    -c --hash           Calculate md5 hash [default: False].
    -r --recursive      Recursive [default: False].
    -V --verbose        Be verbose [default: False].
    -v --version        Show version.
    -h --help           Show this screen.
""".format(BANNER, NAME, CATALOGPATH)


def cmd_index(args, noder, catalog, top):
    path = args['<path>']
    name = args['<name>']
    nohash = not args['--hash']
    subsize = args['--subsize']
    if not os.path.exists(path):
        Logger.err('\"{}\" does not exist'.format(path))
        return False
    if name in noder.get_storage_names(top):
        Logger.err('storage named \"{}\" already exist'.format(name))
        return False
    start = datetime.datetime.now()
    walker = Walker(noder, nohash=nohash)
    root = noder.storage_node(name, path, parent=top, attr=args['--meta'])
    _, cnt = walker.index(path, name, parent=root, parentpath=path)
    if subsize:
        noder.rec_size(root)
    stop = datetime.datetime.now()
    Logger.info('Indexed {} file(s) in {}'.format(cnt, stop-start))
    catalog.save(top)


def cmd_ls(args, noder, top):
    path = args['<path>']
    if not path:
        path = SEPARATOR
    if not path.startswith(SEPARATOR):
        path = SEPARATOR + path
    pre = '{}{}'.format(SEPARATOR, noder.TOPNAME)
    if not path.startswith(pre):
        path = pre + path
    if not path.endswith(SEPARATOR):
        path += SEPARATOR
    if not path.endswith(WILD):
        path += WILD
    return noder.walk(top, path, rec=args['--recursive'])


def cmd_rm(args, noder, catalog, top):
    what = args['<storage>']
    storages = list(x.name for x in top.children)
    if what in storages:
        node = next(filter(lambda x: x.name == what, top.children))
        node.parent = None
        catalog.save(top)
    else:
        Logger.err('Storage named \"{}\" does not exist'.format(what))
    return top


def cmd_find(args, noder, top):
    return noder.find_name(top, args['<term>'], script=args['--script'])


def cmd_tree(args, noder, top):
    path = args['<path>']
    node = top
    if path:
        node = noder.get_node(top, path)
    if node:
        noder.print_tree(node)


def cmd_graph(args, noder, top):
    path = args['<path>']
    if not path:
        path = GRAPHPATH
    cmd = noder.to_dot(top, path)
    Logger.info('create graph with \"{}\" (you need graphviz)'.format(cmd))


def banner():
    Logger.log(BANNER)
    Logger.log("")


def main():
    args = docopt(USAGE, version=VERSION)

    if args['help']:
        print(USAGE)
        return True

    # print banner
    banner()

    # init noder
    noder = Noder(verbose=args['--verbose'])
    # init catalog
    catalog = Catalog(args['--catalog'], verbose=args['--verbose'],
                      force=args['--force'])
    # init top node
    top = catalog.restore()
    if not top:
        top = noder.new_top_node()

    # handle the meta node
    meta = noder.update_metanode(noder.get_meta_node(top))
    catalog.set_metanode(meta)

    # parse command
    if args['index']:
        cmd_index(args, noder, catalog, top)
    elif args['find']:
        cmd_find(args, noder, top)
    elif args['tree']:
        cmd_tree(args, noder, top)
    elif args['ls']:
        cmd_ls(args, noder, top)
    elif args['rm']:
        cmd_rm(args, noder, catalog, top)
    elif args['graph']:
        cmd_graph(args, noder, top)

    return True


if __name__ == '__main__':
    ''' entry point '''
    if main():
        sys.exit(0)
    sys.exit(1)
