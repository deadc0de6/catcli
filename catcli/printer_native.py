"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

Class for printing nodes in native format
"""

import sys

from catcli.nodes import NodeFile, NodeDir, \
    NodeStorage, NodeAny, typcast_node
from catcli.colors import Colors
from catcli.logger import Logger
from catcli.utils import fix_badchars, size_to_str, \
    has_attr, epoch_to_str


COLOR_STORAGE = Colors.YELLOW
COLOR_FILE = Colors.WHITE
COLOR_DIRECTORY = Colors.BLUE
COLOR_ARCHIVE = Colors.PURPLE
COLOR_TS = Colors.CYAN
COLOR_SIZE = Colors.GREEN

FULLPATH_IN_NAME = True


class NativePrinter:
    """a node printer class"""

    STORAGE = 'storage'
    ARCHIVE = 'archive'
    NBFILES = 'nbfiles'

    def print_du(self, node: NodeAny,
                 raw: bool = False) -> None:
        """print du style"""
        typcast_node(node)
        name = node.get_fullpath()
        size = node.nodesize

        line = size_to_str(size, raw=raw).ljust(10, ' ')
        out = f'{COLOR_SIZE}{line}{Colors.RESET}'
        out += ' '
        out += f'{COLOR_FILE}{name}{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    def print_top(self, pre: str, name: str) -> None:
        """print top node"""
        sys.stdout.write(f'{pre}{name}\n')

    def print_storage(self, pre: str,
                      node: NodeStorage,
                      raw: bool = False) -> None:
        """print a storage node"""
        # construct name
        name = node.name
        name = fix_badchars(name)
        # construct attrs
        attrs = []
        # nb files
        attrs.append(f'nbfiles:{len(node.children)}')
        # the children size
        recsize = node.get_rec_size()
        sizestr = size_to_str(recsize, raw=raw)
        attrs.append(f'totsize:{sizestr}')
        # free
        pcent = 0.0
        if node.total > 0:
            pcent = node.free * 100 / node.total
        attrs.append(f'free:{pcent:.1f}%')
        # du
        sztotal = size_to_str(node.total, raw=raw)
        szused = size_to_str(node.total - node.free, raw=raw)
        attrs.append(f'du:{szused}/{sztotal}')
        # timestamp
        if has_attr(node, 'ts'):
            attrs.append(f'date:{epoch_to_str(node.ts)}')

        # print
        out = f'{pre}{Colors.UND}{self.STORAGE}{Colors.RESET}: '
        out += f'{COLOR_STORAGE}{name}{Colors.RESET}'
        if attrs:
            out += f' [{Colors.WHITE}{"|".join(attrs)}{Colors.RESET}]'
        sys.stdout.write(f'{out}\n')

    def print_file(self, pre: str,
                   node: NodeFile,
                   withpath: bool = False,
                   withstorage: bool = False,
                   raw: bool = False) -> None:
        """print a file node"""
        # construct name
        name = node.name
        storage = node.get_storage_node()
        if withpath:
            name = node.get_fullpath()
        # construct attributes
        attrs = []
        if node.md5:
            attrs.append(f'md5:{node.md5}')
        if withstorage:
            content = Logger.get_bold_text(storage.name)
            attrs.append(f'storage:{content}')
        # print
        out = []
        out.append(f'{pre}')
        out.append(f'{COLOR_FILE}{name}{Colors.RESET}')
        size = 0
        if node.nodesize:
            size = node.nodesize
        line = size_to_str(size, raw=raw)
        out.append(f'{COLOR_SIZE}{line}{Colors.RESET}')
        if has_attr(node, 'maccess'):
            line = epoch_to_str(node.maccess)
            out.append(f'{COLOR_TS}{line}{Colors.RESET}')
        if attrs:
            out.append(f'{Colors.GRAY}[{",".join(attrs)}]{Colors.RESET}')

        out = [x for x in out if x]
        sys.stdout.write(f'{" ".join(out)}\n')

    def print_dir(self, pre: str,
                  node: NodeDir,
                  withpath: bool = False,
                  withstorage: bool = False,
                  withnbchildren: bool = False,
                  raw: bool = False) -> None:
        """print a directory node"""
        # construct name
        name = node.name
        storage = node.get_storage_node()
        if withpath:
            name = node.get_fullpath()
        # construct attrs
        attrs = []
        if withnbchildren:
            nbchildren = len(node.children)
            attrs.append(f'{self.NBFILES}:{nbchildren}')
        if withstorage:
            attrs.append(f'storage:{Logger.get_bold_text(storage.name)}')
        # print
        out = []
        out.append(f'{pre}')
        out.append(f'{COLOR_DIRECTORY}{name}{Colors.RESET}')
        size = 0
        if node.nodesize:
            size = node.nodesize
        line = size_to_str(size, raw=raw)
        out.append(f'{COLOR_SIZE}{line}{Colors.RESET}')
        if has_attr(node, 'maccess'):
            line = epoch_to_str(node.maccess)
            out.append(f'{COLOR_TS}{line}{Colors.RESET}')
        if attrs:
            out.append(f'{Colors.GRAY}[{",".join(attrs)}]{Colors.RESET}')

        out = [x for x in out if x]
        sys.stdout.write(f'{" ".join(out)}\n')

    def print_archive(self, pre: str,
                      name: str, archive: str) -> None:
        """print an archive"""
        name = fix_badchars(name)
        out = f'{pre}{COLOR_ARCHIVE}{name}{Colors.RESET} '
        out += f'{Colors.GRAY}[{self.ARCHIVE}:{archive}]{Colors.RESET}'
        sys.stdout.write(f'{out}\n')
