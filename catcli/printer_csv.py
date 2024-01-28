"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2024, deadc0de6

Class for printing nodes in csv format
"""

import sys
from typing import List

from catcli.nodes import NodeAny, NodeStorage, TYPE_DIR
from catcli.utils import size_to_str, epoch_to_str, \
    has_attr


class CsvPrinter:
    """a node printer class"""

    DEFSEP = ','
    CSV_HEADER = ('name,type,path,size,indexed_at,'
                  'maccess,md5,nbfiles,free_space,'
                  'total_space,meta')

    def _print_entries(self, entries: List[str], sep: str = DEFSEP) -> None:
        line = sep.join(['"' + o + '"' for o in entries])
        if len(line) > 0:
            sys.stdout.write(f'{line}\n')

    def print_header(self) -> None:
        """print csv header"""
        sys.stdout.write(f'{self.CSV_HEADER}\n')

    def print_storage(self, node: NodeStorage,
                      sep: str = DEFSEP,
                      raw: bool = False) -> None:
        """print a storage node"""
        out = []
        out.append(node.name)   # name
        out.append(node.type)   # type
        out.append('')          # fake full path
        size = node.get_rec_size()
        out.append(size_to_str(size, raw=raw))  # size
        out.append(epoch_to_str(node.ts))  # indexed_at
        out.append('')  # fake maccess
        out.append('')  # fake md5
        out.append(str(len(node.children)))  # nbfiles
        # fake free_space
        out.append(size_to_str(node.free, raw=raw))
        # fake total_space
        out.append(size_to_str(node.total, raw=raw))
        out.append(node.attr)  # meta
        self._print_entries(out, sep=sep)

    def print_node(self, node: NodeAny,
                   sep: str = DEFSEP,
                   raw: bool = False) -> None:
        """print other nodes"""
        out = []
        out.append(node.name.replace('"', '""'))  # name
        out.append(node.type)  # type
        fullpath = node.get_fullpath()
        out.append(fullpath.replace('"', '""'))  # full path

        out.append(size_to_str(node.nodesize, raw=raw))  # size
        storage = node.get_storage_node()
        out.append(epoch_to_str(storage.ts))  # indexed_at
        if has_attr(node, 'maccess'):
            out.append(epoch_to_str(node.maccess))  # maccess
        else:
            out.append('')  # fake maccess
        if has_attr(node, 'md5'):
            out.append(node.md5)  # md5
        else:
            out.append('')  # fake md5
        if node.type == TYPE_DIR:
            out.append(str(len(node.children)))  # nbfiles
        else:
            out.append('')  # fake nbfiles
        out.append('')  # fake free_space
        out.append('')  # fake total_space
        out.append('')  # fake meta
        self._print_entries(out, sep=sep)
