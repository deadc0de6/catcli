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
from .utils import ask, edit

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
    {1} ls     [--catalog=<path>] [--format=<fmt>] [-aBCrVS] [<path>]
    {1} find   [--catalog=<path>] [--format=<fmt>] [-aBCbdVP] [--path=<path>] <term>
    {1} tree   [--catalog=<path>] [--format=<fmt>] [-aBCVSH] [<path>]
    {1} index  [--catalog=<path>] [--meta=<meta>...] [-aBCcfnV] <name> <path>
    {1} update [--catalog=<path>] [-aBCcfnV] [--lpath=<path>] <name> <path>
    {1} rm     [--catalog=<path>] [-BCfV] <storage>
    {1} rename [--catalog=<path>] [-BCfV] <storage> <name>
    {1} edit   [--catalog=<path>] [-BCfV] <storage>
    {1} graph  [--catalog=<path>] [-BCV] [<path>]
    {1} print_supported_formats
    {1} help
    {1} --help
    {1} --version

Options:
    --catalog=<path>    Path to the catalog [default: {2}].
    --meta=<meta>       Additional attribute to store [default: ].
    -a --archive        Handle archive file [default: False].
    -B --no-banner      Do not display the banner [default: False].
    -b --script         Output script to manage found file(s) [default: False].
    -C --no-color       Do not output colors [default: False].
    -c --hash           Calculate md5 hash [default: False].
    -d --directory      Only directory [default: False].
    -F --format=<fmt>   Print format, see command \"print_supported_formats\" [default: native].
    -f --force          Do not ask when updating the catalog [default: False].
    -H --header         Print header on CSV format [default: False].
    -l --lpath=<path>   Path where changes are logged [default: ]
    -n --no-subsize     Do not store size of directories [default: False].
    -P --parent         Ignore stored relpath [default: True].
    -p --path=<path>    Start path.
    -r --recursive      Recursive [default: False].
    -S --sortsize       Sort by size, largest first [default: False].
    -V --verbose        Be verbose [default: False].
    -v --version        Show version.
    -h --help           Show this screen.
""".format(BANNER, NAME, CATALOGPATH)  # nopep8


def cmd_index(args, noder, catalog, top):
    path = args['<path>']
    name = args['<name>']
    hash = args['--hash']
    debug = args['--verbose']
    subsize = not args['--no-subsize']
    if not os.path.exists(path):
        Logger.err('\"{}\" does not exist'.format(path))
        return
    if name in noder.get_storage_names(top):
        try:
            if not ask('Overwrite storage \"{}\"'.format(name)):
                Logger.err('storage named \"{}\" already exist'.format(name))
                return
        except KeyboardInterrupt:
            Logger.err('aborted')
            return
        node = noder.get_storage_node(top, name)
        node.parent = None

    start = datetime.datetime.now()
    walker = Walker(noder, hash=hash, debug=debug)
    attr = noder.format_storage_attr(args['--meta'])
    root = noder.storage_node(name, path, parent=top, attr=attr)
    _, cnt = walker.index(path, root, name)
    if subsize:
        noder.rec_size(root)
    stop = datetime.datetime.now()
    Logger.info('Indexed {} file(s) in {}'.format(cnt, stop - start))
    if cnt > 0:
        catalog.save(top)


def cmd_update(args, noder, catalog, top):
    path = args['<path>']
    name = args['<name>']
    hash = args['--hash']
    logpath = args['--lpath']
    debug = args['--verbose']
    subsize = not args['--no-subsize']
    if not os.path.exists(path):
        Logger.err('\"{}\" does not exist'.format(path))
        return
    root = noder.get_storage_node(top, name, path=path)
    if not root:
        Logger.err('storage named \"{}\" does not exist'.format(name))
        return
    start = datetime.datetime.now()
    walker = Walker(noder, hash=hash, debug=debug,
                    logpath=logpath)
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
    found = noder.walk(top, path,
                       rec=args['--recursive'],
                       fmt=args['--format'])
    if not found:
        Logger.err('\"{}\": nothing found'.format(args['<path>']))
    return found


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
    fromtree = args['--parent']
    directory = args['--directory']
    startpath = args['--path']
    fmt = args['--format']
    return noder.find_name(top, args['<term>'], script=args['--script'],
                           startpath=startpath, directory=directory,
                           parentfromtree=fromtree, fmt=fmt)


def cmd_tree(args, noder, top):
    path = args['<path>']
    fmt = args['--format']
    hdr = args['--header']

    # find node to start with
    node = top
    if path:
        node = noder.get_node(top, path)

    if node:
        # print the tree
        noder.print_tree(node, fmt=fmt, header=hdr)


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
        node.attr = noder.format_storage_attr(new)
        if catalog.save(top):
            Logger.info('Storage \"{}\" edited'.format(storage))
    else:
        Logger.err('Storage named \"{}\" does not exist'.format(storage))
    return top


def banner():
    Logger.out_err(BANNER)
    Logger.out_err("")


def main():
    args = docopt(USAGE, version=VERSION)

    if args['help'] or args['--help']:
        print(USAGE)
        return True

    if args['print_supported_formats']:
        print('"native": native format')
        print('"csv"   : CSV format')
        print('          {}'.format(Noder.CSV_HEADER))
        return True

    # check format
    fmt = args['--format']
    if fmt != 'native' and fmt != 'csv':
        Logger.err('bad format: {}'.format(fmt))
        return False

    if args['--verbose']:
        print(args)

    # print banner
    if not args['--no-banner']:
        banner()

    # set colors
    if args['--no-color']:
        Logger.no_color()

    # init noder
    noder = Noder(debug=args['--verbose'], sortsize=args['--sortsize'],
                  arc=args['--archive'])
    # init catalog
    catalog = Catalog(args['--catalog'], debug=args['--verbose'],
                      force=args['--force'])
    # init top node
    top = catalog.restore()
    if not top:
        top = noder.new_top_node()

    # handle the meta node
    meta = noder.update_metanode(top)
    catalog.set_metanode(meta)

    # parse command
    if args['index']:
        cmd_index(args, noder, catalog, top)
    if args['update']:
        cmd_update(args, noder, catalog, top)
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
