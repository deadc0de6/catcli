"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

Class that represents a node in the catalog tree
"""
# pylint: disable=W0622

from anytree import NodeMixin  # type: ignore


TYPE_TOP = 'top'
TYPE_FILE = 'file'
TYPE_DIR = 'dir'
TYPE_ARC = 'arc'
TYPE_STORAGE = 'storage'
TYPE_META = 'meta'

NAME_TOP = 'top'
NAME_META = 'meta'


class Node(NodeMixin):  # type: ignore
    """a node in the catalog"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 type: str,
                 size: float = 0,
                 relpath: str = '',
                 md5: str = '',
                 maccess: float = 0,
                 free: int = 0,
                 total: int = 0,
                 indexed_dt: int = 0,
                 attr: str = '',
                 archive: str = '',
                 parent=None,
                 children=None):
        """build a node"""
        super().__init__()
        self.name = name
        self.type = type
        self.size = size
        self.relpath = relpath
        self.md5 = md5
        self.maccess = maccess
        self.free = free
        self.total = total
        self.indexed_dt = indexed_dt
        self.attr = attr
        self.archive = archive
        self.parent = parent
        if children:
            self.children = children
        self._flagged = False

    def flagged(self) -> bool:
        """is flagged"""
        return self._flagged

    def flag(self) -> None:
        """flag a node"""
        self._flagged = True

    def unflag(self) -> None:
        """unflag node"""
        self._flagged = False
