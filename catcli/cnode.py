"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

Class that represents a node in the catalog tree
"""
# pylint: disable=W0622

from typing import Dict, Any
from anytree import NodeMixin  # type: ignore


_TYPE_BAD = 'badtype'
_TYPE_TOP = 'top'
_TYPE_FILE = 'file'
_TYPE_DIR = 'dir'
_TYPE_ARC = 'arc'
_TYPE_STORAGE = 'storage'
_TYPE_META = 'meta'

NAME_TOP = 'top'
NAME_META = 'meta'


class NodeAny(NodeMixin):  # type: ignore
    """generic node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 parent=None,
                 children=None):
        """build generic node"""
        super().__init__()
        self._flagged = False
        self.parent = parent
        if children:
            self.children = children

    def flagged(self) -> bool:
        """is flagged"""
        if not hasattr(self, '_flagged'):
            return False
        return self._flagged

    def flag(self) -> None:
        """flag a node"""
        self._flagged = True

    def unflag(self) -> None:
        """unflag node"""
        self._flagged = False
        del self._flagged


class NodeTop(NodeAny):
    """a top node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 children=None):
        """build a top node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = _TYPE_TOP
        self.parent = None
        if children:
            self.children = children


class NodeFile(NodeAny):
    """a file node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 relpath: str,
                 size: int,
                 md5: str,
                 maccess: float,
                 parent=None,
                 children=None):
        """build a file node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = _TYPE_FILE
        self.relpath = relpath
        self.size = size
        self.md5 = md5
        self.maccess = maccess
        self.parent = parent
        if children:
            self.children = children


class NodeDir(NodeAny):
    """a directory node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 relpath: str,
                 size: int,
                 maccess: float,
                 parent=None,
                 children=None):
        """build a directory node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = _TYPE_DIR
        self.relpath = relpath
        self.size = size
        self.maccess = maccess
        self.parent = parent
        if children:
            self.children = children


class NodeArchived(NodeAny):
    """an archived node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 relpath: str,
                 size: int,
                 md5: str,
                 archive: str,
                 parent=None,
                 children=None):
        """build an archived node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = _TYPE_ARC
        self.relpath = relpath
        self.size = size
        self.md5 = md5
        self.archive = archive
        self.parent = parent
        if children:
            self.children = children


class NodeStorage(NodeAny):
    """a storage node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 free: int,
                 total: int,
                 size: int,
                 indexed_dt: float,
                 attr: Dict[str, Any],
                 parent=None,
                 children=None):
        """build a storage node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = _TYPE_STORAGE
        self.free = free
        self.total = total
        self.attr = attr
        self.size = size
        self.indexed_dt = indexed_dt
        self.parent = parent
        if children:
            self.children = children


class NodeMeta(NodeAny):
    """a meta node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 attr: str,
                 parent=None,
                 children=None):
        """build a meta node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = _TYPE_META
        self.attr = attr
        self.parent = parent
        if children:
            self.children = children
