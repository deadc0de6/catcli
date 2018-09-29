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
from .utils import *

NAME = 'catcli'
CUR = os.path.dirname(os.path.abspath(__file__))
CATALOGPATH = '{}.catalog'.format(NAME)
GRAPHPATH = '/tmp/{}.dot'.format(NAME)
SEPARATOR = '/'
WILD = '*'

BANNER = """ +-+-+-+-+-+-+
 |c|a|t|c|l|i|
 +-+-+-+-+-+-+ v{}""".format(VERSION)

USAGE = """
{0}

Usage:
    {1} index  [--catalog=<path>] [--meta=<meta>...] [-acfuV] <name> <path>
    {1} update [--catalog=<path>] [-acfuV] <name> <path>
    {1} ls     [--catalog=<path>] [-arVS] [<path>]
    {1} find   [--catalog=<path>] [-abV] <term>
    {1} rm     [--catalog=<path>] [-fV] <storage>
    {1} tree   [--catalog=<path>] [-aVS] [<path>]
    {1} rename [--catalog=<path>] [-fV] <storage> <name>
    {1} edit   [--catalog=<path>] [-fV] <storage>
    {1} graph  [--catalog=<path>] [-V] [<path>]
    {1} help
    {1} --help
    {1} --version

Options:
    --catalog=<path>  Path to the catalog [default: {2}].
    --meta=<meta>     Additional attribute to store [default: ].
    -u --subsize      Store size of directories [default: False].
    -a --archive      Handle archive file [default: False].
    -f --force        Do not ask when updating the catalog [default: False].
    -b --script       Output script to manage found file(s) [default: False].
    -S --sortsize     Sort by size, largest first [default: False].
    -c --hash         Calculate md5 hash [default: False].
    -r --recursive    Recursive [default: False].
    -V --verbose      Be verbose [default: False].
    -v --version      Show version.
    -h --help         Show this screen.
""".format(BANNER, NAME, CATALOGPATH)


def cmd_index(args, noder, catalog, top, debug=False):
    path = args['<path>']
    name = args['<name>']
    nohash = not args['--hash']
    subsize = args['--subsize']
    if not os.path.exists(path):
        Logger.err('\"{}\" does not exist'.format(path))
        return
    if name in noder.get_storage_names(top):
        if not ask('Overwrite storage \"{}\"'.format(name)):
            Logger.err('storage named \"{}\" already exist'.format(name))
            return
        node = noder.get_storage_node(top, name)
        node.parent = None
    start = datetime.datetime.now()
    walker = Walker(noder, nohash=nohash, debug=debug)
    attr = noder.format_storage_attr(args['--meta'])
    root = noder.storage_node(name, path, parent=top, attr=attr)
    _, cnt = walker.index(path, root, name)
    if subsize:
        noder.rec_size(root)
    stop = datetime.datetime.now()
    Logger.info('Indexed {} file(s) in {}'.format(cnt, stop - start))
    if cnt > 0:
        catalog.save(top)


def cmd_update(args, noder, catalog, top, debug=False):
    path = args['<path>']
    name = args['<name>']
    nohash = not args['--hash']
    subsize = args['--subsize']
    if not os.path.exists(path):
        Logger.err('\"{}\" does not exist'.format(path))
        return
    root = noder.get_storage_node(top, name)
    if not root:
        Logger.err('storage named \"{}\" does not exist'.format(name))
        return
    start = datetime.datetime.now()
    walker = Walker(noder, nohash=nohash, debug=debug)
    cnt = walker.reindex(path, root, top)
    if subsize:
        noder.rec_size(root)
    stop = datetime.datetime.now()
    Logger.info('updated {} file(s) in {}'.format(cnt, stop - start))
    if cnt > 0:
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
    name = args['<storage>']
    node = noder.get_storage_node(top, name)
    if node:
        node.parent = None
        if catalog.save(top):
            Logger.info('Storage \"{}\" removed'.format(name))
    else:
        Logger.err('Storage named \"{}\" does not exist'.format(name))
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


def cmd_rename(args, noder, catalog, top):
    storage = args['<storage>']
    new = args['<name>']
    storages = list(x.name for x in top.children)
    if storage in storages:
        node = next(filter(lambda x: x.name == storage, top.children))
        node.name = new
        if catalog.save(top):
            m = 'Storage \"{}\" renamed to \"{}\"'.format(storage, new)
            Logger.info(m)
    else:
        Logger.err('Storage named \"{}\" does not exist'.format(storage))
    return top


def cmd_edit(args, noder, catalog, top):
    storage = args['<storage>']
    storages = list(x.name for x in top.children)
    if storage in storages:
        node = next(filter(lambda x: x.name == storage, top.children))
        attr = node.attr
        if not attr:
            attr = ''
        new = edit(attr)
        node.attr = noder.clean_storage_attr(new)
        if catalog.save(top):
            Logger.info('Storage \"{}\" edited'.format(storage))
    else:
        Logger.err('Storage named \"{}\" does not exist'.format(storage))
    return top


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
    noder = Noder(verbose=args['--verbose'], sortsize=args['--sortsize'],
                  arc=args['--archive'])
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
        cmd_index(args, noder, catalog, top, debug=args['--verbose'])
    if args['update']:
        cmd_update(args, noder, catalog, top, debug=args['--verbose'])
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
    elif args['rename']:
        cmd_rename(args, noder, catalog, top)
    elif args['edit']:
        cmd_edit(args, noder, catalog, top)

    return True


if __name__ == '__main__':
    '''entry point'''
    if main():
        sys.exit(0)
    sys.exit(1)
