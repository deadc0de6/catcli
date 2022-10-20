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
from .version import __version__ as VERSION
from .logger import Logger
from .catalog import Catalog
from .walker import Walker
from .noder import Noder
from .utils import ask, edit

NAME = 'catcli'
CUR = os.path.dirname(os.path.abspath(__file__))
CATALOGPATH = f'{NAME}.catalog'
GRAPHPATH = f'/tmp/{NAME}.dot'
SEPARATOR = '/'
WILD = '*'
FORMATS = ['native', 'csv', 'fzf-native', 'fzf-csv']

BANNER = f""" +-+-+-+-+-+-+
 |c|a|t|c|l|i|
 +-+-+-+-+-+-+ v{VERSION}"""

USAGE = f"""
{BANNER}

Usage:
    {NAME} ls     [--catalog=<path>] [--format=<fmt>] [-aBCrVSs] [<path>]
    {NAME} find   [--catalog=<path>] [--format=<fmt>] [-aBCbdVsP] [--path=<path>] [<term>]
    {NAME} tree   [--catalog=<path>] [-aBCVSsH] [<path>]
    {NAME} index  [--catalog=<path>] [--meta=<meta>...] [-aBCcfnV] <name> <path>
    {NAME} update [--catalog=<path>] [-aBCcfnV] [--lpath=<path>] <name> <path>
    {NAME} rm     [--catalog=<path>] [-BCfV] <storage>
    {NAME} rename [--catalog=<path>] [-BCfV] <storage> <name>
    {NAME} edit   [--catalog=<path>] [-BCfV] <storage>
    {NAME} graph  [--catalog=<path>] [-BCV] [<path>]
    {NAME} print_supported_formats
    {NAME} help
    {NAME} --help
    {NAME} --version

Options:
    --catalog=<path>    Path to the catalog [default: {CATALOGPATH}].
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
    -s --raw-size       Print raw size rather than human readable [default: False].
    -S --sortsize       Sort by size, largest first [default: False].
    -V --verbose        Be verbose [default: False].
    -v --version        Show version.
    -h --help           Show this screen.
"""  # nopep8


def cmd_index(args, noder, catalog, top):
    """index action"""
    path = args['<path>']
    name = args['<name>']
    usehash = args['--hash']
    debug = args['--verbose']
    subsize = not args['--no-subsize']
    if not os.path.exists(path):
        Logger.err(f'\"{path}\" does not exist')
        return
    if name in noder.get_storage_names(top):
        try:
            if not ask(f'Overwrite storage \"{name}\"'):
                Logger.err(f'storage named \"{name}\" already exist')
                return
        except KeyboardInterrupt:
            Logger.err('aborted')
            return
        node = noder.get_storage_node(top, name)
        node.parent = None

    start = datetime.datetime.now()
    walker = Walker(noder, usehash=usehash, debug=debug)
    attr = noder.format_storage_attr(args['--meta'])
    root = noder.storage_node(name, path, parent=top, attr=attr)
    _, cnt = walker.index(path, root, name)
    if subsize:
        noder.rec_size(root)
    stop = datetime.datetime.now()
    diff = stop - start
    Logger.info(f'Indexed {cnt} file(s) in {diff}')
    if cnt > 0:
        catalog.save(top)


def cmd_update(args, noder, catalog, top):
    """update action"""
    path = args['<path>']
    name = args['<name>']
    usehash = args['--hash']
    logpath = args['--lpath']
    debug = args['--verbose']
    subsize = not args['--no-subsize']
    if not os.path.exists(path):
        Logger.err(f'\"{path}\" does not exist')
        return
    root = noder.get_storage_node(top, name, path=path)
    if not root:
        Logger.err(f'storage named \"{name}\" does not exist')
        return
    start = datetime.datetime.now()
    walker = Walker(noder, usehash=usehash, debug=debug,
                    logpath=logpath)
    cnt = walker.reindex(path, root, top)
    if subsize:
        noder.rec_size(root)
    stop = datetime.datetime.now()
    diff = stop - start
    Logger.info(f'updated {cnt} file(s) in {diff}')
    if cnt > 0:
        catalog.save(top)


def cmd_ls(args, noder, top):
    """ls action"""
    path = args['<path>']
    if not path:
        path = SEPARATOR
    if not path.startswith(SEPARATOR):
        path = SEPARATOR + path
    pre = f'{SEPARATOR}{noder.TOPNAME}'
    if not path.startswith(pre):
        path = pre + path
    if not path.endswith(SEPARATOR):
        path += SEPARATOR
    if not path.endswith(WILD):
        path += WILD
    found = noder.walk(top, path,
                       rec=args['--recursive'],
                       fmt=args['--format'],
                       raw=args['--raw-size'])
    if not found:
        path = args['<path>']
        Logger.err(f'\"{path}\": nothing found')
    return found


def cmd_rm(args, noder, catalog, top):
    """rm action"""
    name = args['<storage>']
    node = noder.get_storage_node(top, name)
    if node:
        node.parent = None
        if catalog.save(top):
            Logger.info(f'Storage \"{name}\" removed')
    else:
        Logger.err(f'Storage named \"{name}\" does not exist')
    return top


def cmd_find(args, noder, top):
    """find action"""
    fromtree = args['--parent']
    directory = args['--directory']
    startpath = args['--path']
    fmt = args['--format']
    raw = args['--raw-size']
    script = args['--script']
    search_for = args['<term>']
    return noder.find_name(top, search_for, script=script,
                           startpath=startpath, directory=directory,
                           parentfromtree=fromtree, fmt=fmt, raw=raw)


def cmd_tree(args, noder, top):
    """tree action"""
    path = args['<path>']
    hdr = args['--header']
    raw = args['--raw-size']

    # find node to start with
    node = top
    if path:
        node = noder.get_node(top, path)

    if node:
        # print the tree
        noder.print_tree(top, node, header=hdr, raw=raw)


def cmd_graph(args, noder, top):
    """graph action"""
    path = args['<path>']
    if not path:
        path = GRAPHPATH
    cmd = noder.to_dot(top, path)
    Logger.info(f'create graph with \"{cmd}\" (you need graphviz)')


def cmd_rename(args, catalog, top):
    """rename action"""
    storage = args['<storage>']
    new = args['<name>']
    storages = list(x.name for x in top.children)
    if storage in storages:
        node = next(filter(lambda x: x.name == storage, top.children))
        node.name = new
        if catalog.save(top):
            msg = f'Storage \"{storage}\" renamed to \"{new}\"'
            Logger.info(msg)
    else:
        Logger.err(f'Storage named \"{storage}\" does not exist')
    return top


def cmd_edit(args, noder, catalog, top):
    """edit action"""
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
            Logger.info(f'Storage \"{storage}\" edited')
    else:
        Logger.err(f'Storage named \"{storage}\" does not exist')
    return top


def banner():
    """print banner"""
    Logger.out_err(BANNER)
    Logger.out_err("")


def print_supported_formats():
    """print all supported formats to stdout"""
    print('"native"     : native format')
    print('"csv"        : CSV format')
    print(f'               {Noder.CSV_HEADER}')
    print('"fzf-native" : fzf with native output for selected entries')
    print('"fzf-csv"    : fzf with native output for selected entries')


def main():
    """entry point"""
    args = docopt(USAGE, version=VERSION)

    if args['help'] or args['--help']:
        print(USAGE)
        return True

    if args['print_supported_formats']:
        print_supported_formats()
        return True

    # check format
    fmt = args['--format']
    if fmt not in FORMATS:
        Logger.err(f'bad format: {fmt}')
        print_supported_formats()
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
        cmd_rename(args, catalog, top)
    elif args['edit']:
        cmd_edit(args, noder, catalog, top)

    return True


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
