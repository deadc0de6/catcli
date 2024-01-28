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
from typing import Dict, Any, List, \
    Tuple
from docopt import docopt
import cmd2

# local imports
from catcli.version import __version__ as VERSION
from catcli.nodes import NodeTop, NodeAny
from catcli.logger import Logger
from catcli.printer_csv import CsvPrinter
from catcli.colors import Colors
from catcli.catalog import Catalog
from catcli.walker import Walker
from catcli.noder import Noder
from catcli.utils import ask, edit, path_to_search_all
from catcli.exceptions import BadFormatException, CatcliException

NAME = 'catcli'
CUR = os.path.dirname(os.path.abspath(__file__))
CATALOGPATH = f'{NAME}.catalog'
GRAPHPATH = f'/tmp/{NAME}.dot'
FORMATS = ['native', 'csv', 'csv-with-header', 'fzf-native', 'fzf-csv']

BANNER = f""" +-+-+-+-+-+-+
 |c|a|t|c|l|i|
 +-+-+-+-+-+-+ v{VERSION}"""

USAGE = f"""
{BANNER}

Usage:
    {NAME} ls       [--catalog=<path>] [--format=<fmt>] [-aBCrVSs] [<path>]
    {NAME} tree     [--catalog=<path>] [-aBCVSs] [<path>]
    {NAME} find     [--catalog=<path>] [--format=<fmt>]
                    [-aBCbdVs] [--path=<path>] [<term>]
    {NAME} index    [--catalog=<path>] [--meta=<meta>...]
                    [-aBCcfV] <name> <path>
    {NAME} update   [--catalog=<path>] [-aBCcfV]
                    [--lpath=<path>] <name> <path>
    {NAME} mount    [--catalog=<path>] [-V] <mountpoint>
    {NAME} du       [--catalog=<path>] [-BCVSs] [<path>]
    {NAME} rm       [--catalog=<path>] [-BCfV] <storage>
    {NAME} rename   [--catalog=<path>] [-BCfV] <storage> <name>
    {NAME} edit     [--catalog=<path>] [-BCfV] <storage>
    {NAME} graph    [--catalog=<path>] [-BCV] [<path>]
    {NAME}          [--catalog=<path>]
    {NAME} fixsizes [--catalog=<path>]
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
    -F --format=<fmt>   see \"print_supported_formats\" [default: native].
    -f --force          Do not ask when updating the catalog [default: False].
    -l --lpath=<path>   Path where changes are logged [default: ]
    -p --path=<path>    Start path.
    -r --recursive      Recursive [default: False].
    -s --raw-size       Print raw size [default: False].
    -S --sortsize       Sort by size, largest first [default: False].
    -V --verbose        Be verbose [default: False].
    -v --version        Show version.
    -h --help           Show this screen.
"""  # nopep8


def cmd_mount(args: Dict[str, Any],
              top: NodeTop,
              noder: Noder) -> bool:
    """mount action"""
    mountpoint = args['<mountpoint>']
    debug = args['--verbose']
    try:
        from catcli.fuser import Fuser  # pylint: disable=C0415
        Fuser(mountpoint, top, noder,
              debug=debug)
    except ModuleNotFoundError:
        Logger.err('install fusepy to use mount')
        return False
    return True


def cmd_index(args: Dict[str, Any],
              noder: Noder,
              catalog: Catalog,
              top: NodeTop) -> None:
    """index action"""
    path = args['<path>']
    name = args['<name>']
    usehash = args['--hash']
    debug = args['--verbose']
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
        node = top.get_storage_node()
        if node:
            node.parent = None

    start = datetime.datetime.now()
    walker = Walker(noder, usehash=usehash, debug=debug)
    attr = args['--meta']
    root = noder.new_storage_node(name, path, top, attr)
    _, cnt = walker.index(path, root, name)
    root.nodesize = root.get_rec_size()
    stop = datetime.datetime.now()
    diff = stop - start
    Logger.info(f'Indexed {cnt} file(s) in {diff}')
    if cnt > 0:
        catalog.save(top)


def cmd_update(args: Dict[str, Any],
               noder: Noder,
               catalog: Catalog,
               top: NodeTop) -> None:
    """update action"""
    path = args['<path>']
    name = args['<name>']
    usehash = args['--hash']
    logpath = args['--lpath']
    debug = args['--verbose']
    if not os.path.exists(path):
        Logger.err(f'\"{path}\" does not exist')
        return
    storage = noder.find_storage_node_by_name(top, name)
    if not storage:
        Logger.err(f'storage named \"{name}\" does not exist')
        return
    noder.update_storage_path(top, name, path)
    start = datetime.datetime.now()
    walker = Walker(noder, usehash=usehash, debug=debug,
                    logpath=logpath)
    cnt = walker.reindex(path, storage, top)
    storage.nodesize = storage.get_rec_size()
    stop = datetime.datetime.now()
    diff = stop - start
    Logger.info(f'updated {cnt} file(s) in {diff}')
    if cnt > 0:
        catalog.save(top)


def cmd_du(args: Dict[str, Any],
           noder: Noder,
           top: NodeTop) -> List[NodeAny]:
    """du action"""
    path = path_to_search_all(args['<path>'])
    found = noder.diskusage(top,
                            path,
                            raw=args['--raw-size'])
    if not found:
        path = args['<path>']
        Logger.err(f'\"{path}\": nothing found')
    return found


def cmd_ls(args: Dict[str, Any],
           noder: Noder,
           top: NodeTop) -> List[NodeAny]:
    """ls action"""
    path = path_to_search_all(args['<path>'])
    fmt = args['--format']
    if fmt.startswith('fzf'):
        raise BadFormatException('fzf is not supported in ls, use find')
    found = noder.list(top,
                       path,
                       fmt=fmt,
                       rec=args['--recursive'],
                       raw=args['--raw-size'])
    if not found:
        path = args['<path>']
        Logger.err(f'\"{path}\": nothing found')
    return found


def cmd_rm(args: Dict[str, Any],
           noder: Noder,
           catalog: Catalog,
           top: NodeTop) -> NodeTop:
    """rm action"""
    name = args['<storage>']
    node = noder.find_storage_node_by_name(top, name)
    if node:
        node.parent = None
        if catalog.save(top):
            Logger.info(f'Storage \"{name}\" removed')
    else:
        Logger.err(f'Storage named \"{name}\" does not exist')
    return top


def cmd_find(args: Dict[str, Any],
             noder: Noder,
             top: NodeTop) -> List[NodeAny]:
    """find action"""
    directory = args['--directory']
    startpath = args['--path']
    fmt = args['--format']
    raw = args['--raw-size']
    script = args['--script']
    search_for = args['<term>']
    if args['--verbose']:
        Logger.debug(f'search for \"{search_for}\" under \"{top.name}\"')
    found = noder.find(top, search_for,
                       script=script,
                       startnode=startpath,
                       only_dir=directory,
                       fmt=fmt,
                       raw=raw)
    return found


def cmd_graph(args: Dict[str, Any],
              noder: Noder,
              top: NodeTop) -> None:
    """graph action"""
    path = args['<path>']
    if not path:
        path = GRAPHPATH
    cmd = noder.to_dot(top, path)
    Logger.info(f'create graph with \"{cmd}\" (you need graphviz)')


def cmd_fixsizes(top: NodeTop,
                 noder: Noder,
                 catalog: Catalog) -> None:
    """
    fix each node size by re-calculating
    recursively their size
    """
    noder.fixsizes(top)
    catalog.save(top)


def cmd_rename(args: Dict[str, Any],
               catalog: Catalog,
               top: NodeTop) -> None:
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


def cmd_edit(args: Dict[str, Any],
             noder: Noder,
             catalog: Catalog,
             top: NodeTop) -> None:
    """edit action"""
    storage = args['<storage>']
    storages = list(x.name for x in top.children)
    if storage in storages:
        node = next(filter(lambda x: x.name == storage, top.children))
        attr = node.attr
        if not attr:
            attr = ''
        new = edit(attr)
        node.attr = noder.attrs_to_string(new)
        if catalog.save(top):
            Logger.info(f'Storage \"{storage}\" edited')
    else:
        Logger.err(f'Storage named \"{storage}\" does not exist')


class CatcliRepl(cmd2.Cmd):  # type: ignore
    """catcli repl"""

    prompt = 'catcli> '
    intro = ''

    def __init__(self) -> None:
        super().__init__()
        # remove built-ins
        del cmd2.Cmd.do_alias
        del cmd2.Cmd.do_edit
        del cmd2.Cmd.do_macro
        del cmd2.Cmd.do_run_pyscript
        del cmd2.Cmd.do_run_script
        del cmd2.Cmd.do_set
        del cmd2.Cmd.do_shell
        del cmd2.Cmd.do_shortcuts
        self.hidden_commands.append('EOF')

    def cmdloop(self, intro: Any = None) -> Any:
        return cmd2.Cmd.cmdloop(self, intro)

    @cmd2.with_argument_list  # type: ignore
    def do_ls(self, arglist: List[str]) -> bool:
        """ls <path>"""
        arglist.insert(0, '--no-banner')
        arglist.insert(0, 'ls')
        args, noder, _, _, top = init(arglist)
        cmd_ls(args, noder, top)
        return False

    @cmd2.with_argument_list  # type: ignore
    def do_tree(self, arglist: List[str]) -> bool:
        """tree <path>"""
        arglist.insert(0, '--no-banner')
        arglist.insert(0, 'tree')
        args, noder, _, _, top = init(arglist)
        cmd_ls(args, noder, top)
        return False

    @cmd2.with_argument_list  # type: ignore
    def do_find(self, arglist: List[str]) -> bool:
        """find <term>"""
        arglist.insert(0, '--no-banner')
        arglist.insert(0, 'find')
        args, noder, _, _, top = init(arglist)
        cmd_find(args, noder, top)
        return False

    @cmd2.with_argument_list  # type: ignore
    def do_du(self, arglist: List[str]) -> bool:
        """du <path>"""
        arglist.insert(0, '--no-banner')
        arglist.insert(0, 'du')
        args, noder, _, _, top = init(arglist)
        cmd_du(args, noder, top)
        return False

    def do_help(self, _: Any) -> bool:
        """help"""
        print(USAGE)
        return False

    # pylint: disable=C0103
    def do_EOF(self, _: Any) -> bool:
        """exit repl"""
        return True


def banner() -> None:
    """print banner"""
    Logger.stderr_nocolor(BANNER)
    Logger.stderr_nocolor("")


def print_supported_formats() -> None:
    """print all supported formats to stdout"""
    print('"native"     : native format')
    print('"csv"        : CSV format')
    print(f'               {CsvPrinter.CSV_HEADER}')
    print('"fzf-native" : fzf to native (only valid for find)')
    print('"fzf-csv"    : fzf to csv (only valid for find)')


def init(argv: List[str]) -> Tuple[Dict[str, Any],
                                   Noder,
                                   Catalog,
                                   str,
                                   NodeTop]:
    """parse catcli arguments"""
    args = docopt(USAGE, argv=argv, version=VERSION)

    if args['help'] or args['--help']:
        print(USAGE)
        sys.exit(0)

    if args['print_supported_formats']:
        print_supported_formats()
        sys.exit(0)

    fmt = args['--format']
    if fmt not in FORMATS:
        Logger.err(f'bad format: {fmt}')
        print_supported_formats()
        sys.exit(0)

    if args['--verbose']:
        print(f'args: {args}')

    # print banner
    if not args['--no-banner']:
        banner()

    # set colors
    if args['--no-color']:
        Colors.no_color()

    # init noder
    noder = Noder(debug=args['--verbose'], sortsize=args['--sortsize'],
                  arc=args['--archive'])
    # init catalog
    catalog_path = args['--catalog']
    catalog = Catalog(catalog_path, debug=args['--verbose'],
                      force=args['--force'])
    # init top node
    top = catalog.restore()
    if not top:
        top = noder.new_top_node()

    # handle the meta node
    meta = noder.update_metanode(top)
    catalog.set_metanode(meta)

    return args, noder, catalog, catalog_path, top


def main() -> bool:
    """entry point"""
    args, noder, catalog, catalog_path, top = init(sys.argv[1:])

    # parse command
    try:
        if args['index']:
            cmd_index(args, noder, catalog, top)
        elif args['update']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_update(args, noder, catalog, top)
            cmd_fixsizes(top, noder, catalog)
        elif args['find']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_find(args, noder, top)
        elif args['ls']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_ls(args, noder, top)
        elif args['tree']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            args['--recursive'] = True
            cmd_ls(args, noder, top)
        elif args['mount']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            if not cmd_mount(args, top, noder):
                return False
        elif args['rm']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_rm(args, noder, catalog, top)
        elif args['graph']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_graph(args, noder, top)
        elif args['rename']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_rename(args, catalog, top)
        elif args['edit']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_edit(args, noder, catalog, top)
        elif args['du']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_du(args, noder, top)
        elif args['fixsizes']:
            if not catalog.exists():
                Logger.err(f'no such catalog: {catalog_path}')
                return False
            cmd_fixsizes(top, noder, catalog)
        else:
            CatcliRepl().cmdloop()
    except CatcliException as exc:
        Logger.stderr_nocolor('ERROR ' + str(exc))
        return False

    return True


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
