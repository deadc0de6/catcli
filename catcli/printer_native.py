"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

Class for printing nodes in native format
"""

import sys
import os

from catcli.nodes import NodeFile, NodeDir, NodeStorage
from catcli.colors import Colors
from catcli.logger import Logger
from catcli.utils import fix_badchars, size_to_str, \
    has_attr, epoch_to_ls_str


TS_LJUST = 13
SIZE_LJUST = 6
NAME_LJUST = 20

class NativePrinter:
    """a node printer class"""

    STORAGE = 'storage'
    ARCHIVE = 'archive'
    NBFILES = 'nbfiles'

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
            attrs.append(f'date:{epoch_to_ls_str(node.ts)}')

        # print
        out = f'{pre}{Colors.UND}{self.STORAGE}{Colors.RESET}: '
        out += f'{Colors.PURPLE}{name}{Colors.RESET}'
        if attrs:
            out += f'\n{" "*len(name)}{Colors.GRAY}{"|".join(attrs)}{Colors.RESET}'
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
            name = os.sep.join([
                storage.name,
                node.parent.get_parent_hierarchy(),
                name])
        name = fix_badchars(name)
        # construct attributes
        attrs = []
        if node.md5:
            attrs.append(f'md5:{node.md5}')
        if withstorage:
            content = Logger.get_bold_text(storage.name)
            attrs.append(f', storage:{content}')
        # print
        out = []
        out .append(f'{pre}')
        line = name.ljust(NAME_LJUST, ' ')
        out.append(f'{line}')
        size = 0
        if node.nodesize:
            size = node.nodesize
        line = size_to_str(size, raw=raw).ljust(SIZE_LJUST, ' ')
        out.append(f'{Colors.BLUE}{line}{Colors.RESET}')
        line = epoch_to_ls_str(node.maccess).ljust(TS_LJUST, ' ')
        out.append(f'{Colors.PURPLE}{line}{Colors.RESET}')
        if attrs:
            out.append(f'{Colors.GRAY}[{",".join(attrs)}]{Colors.RESET}')
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
            name = os.sep.join([
                storage.name,
                node.parent.get_parent_hierarchy(),
                name])
        name = fix_badchars(name)
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
        line = name.ljust(NAME_LJUST, ' ')
        out.append(f'{Colors.BLUE}{line}{Colors.RESET}')
        size = 0
        if node.nodesize:
            size = node.nodesize
        line = size_to_str(size, raw=raw).ljust(SIZE_LJUST, ' ')
        out.append(f'{Colors.GRAY}{line}{Colors.RESET}')
        line = epoch_to_ls_str(node.maccess).ljust(TS_LJUST, ' ')
        out.append(f'{Colors.GRAY}{line}{Colors.RESET}')
        if attrs:
            out.append(f'{Colors.GRAY}[{",".join(attrs)}]{Colors.RESET}')
        sys.stdout.write(f'{" ".join(out)}\n')

    def print_archive(self, pre: str,
                      name: str, archive: str) -> None:
        """print an archive"""
        name = fix_badchars(name)
        out = f'{pre}{Colors.YELLOW}{name}{Colors.RESET} '
        out += f'{Colors.GRAY}[{self.ARCHIVE}:{archive}]{Colors.RESET}'
        sys.stdout.write(f'{out}\n')
