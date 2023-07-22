"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

Class that represents a node in the catalog tree
"""
# pylint: disable=W0622

from typing import Dict, Any
from anytree import NodeMixin  # type: ignore


TYPE_TOP = 'top'
TYPE_FILE = 'file'
TYPE_DIR = 'dir'
TYPE_ARCHIVED = 'arc'
TYPE_STORAGE = 'storage'
TYPE_META = 'meta'

NAME_TOP = 'top'
NAME_META = 'meta'


def typcast_node(node: Any) -> None:
    """typecast node to its sub type"""
    if node.type == TYPE_TOP:
        node.__class__ = NodeTop
    elif node.type == TYPE_FILE:
        node.__class__ = NodeFile
    elif node.type == TYPE_DIR:
        node.__class__ = NodeDir
    elif node.type == TYPE_ARCHIVED:
        node.__class__ = NodeArchived
    elif node.type == TYPE_STORAGE:
        node.__class__ = NodeStorage
    elif node.type == TYPE_META:
        node.__class__ = NodeMeta


class NodeAny(NodeMixin):  # type: ignore
    """generic node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 parent=None,
                 children=None):
        """build generic node"""
        super().__init__()
        self.parent = parent
        if children:
            self.children = children

    def _to_str(self) -> str:
        ret = str(self.__class__) + ": " + str(self.__dict__)
        if self.children:
            ret += '\n'
        for child in self.children:
            ret += f'  child => {child}\n'
        return ret

    def __str__(self) -> str:
        return self._to_str()

    def flagged(self) -> bool:
        """is flagged"""
        if not hasattr(self, '_flagged'):
            return False
        return self._flagged

    def flag(self) -> None:
        """flag a node"""
        self._flagged = True  # pylint: disable=W0201

    def unflag(self) -> None:
        """unflag node"""
        self._flagged = False  # pylint: disable=W0201
        delattr(self, '_flagged')


class NodeTop(NodeAny):
    """a top node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 children=None):
        """build a top node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = TYPE_TOP
        self.parent = None
        if children:
            self.children = children

    def __str__(self) -> str:
        return self._to_str()


class NodeFile(NodeAny):
    """a file node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 relpath: str,
                 nodesize: int,
                 md5: str,
                 maccess: float,
                 parent=None,
                 children=None):
        """build a file node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = TYPE_FILE
        self.relpath = relpath
        self.nodesize = nodesize
        self.md5 = md5
        self.maccess = maccess
        self.parent = parent
        if children:
            self.children = children

    def __str__(self) -> str:
        return self._to_str()


class NodeDir(NodeAny):
    """a directory node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 relpath: str,
                 nodesize: int,
                 maccess: float,
                 parent=None,
                 children=None):
        """build a directory node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = TYPE_DIR
        self.relpath = relpath
        self.nodesize = nodesize
        self.maccess = maccess
        self.parent = parent
        if children:
            self.children = children

    def __str__(self) -> str:
        return self._to_str()


class NodeArchived(NodeAny):
    """an archived node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 relpath: str,
                 nodesize: int,
                 md5: str,
                 archive: str,
                 parent=None,
                 children=None):
        """build an archived node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = TYPE_ARCHIVED
        self.relpath = relpath
        self.nodesize = nodesize
        self.md5 = md5
        self.archive = archive
        self.parent = parent
        if children:
            self.children = children

    def __str__(self) -> str:
        return self._to_str()


class NodeStorage(NodeAny):
    """a storage node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 free: int,
                 total: int,
                 nodesize: int,
                 ts: float,
                 attr: str,
                 parent=None,
                 children=None):
        """build a storage node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = TYPE_STORAGE
        self.free = free
        self.total = total
        self.attr = attr
        self.nodesize = nodesize
        self.ts = ts  # pylint: disable=C0103
        self.parent = parent
        if children:
            self.children = children

    def __str__(self) -> str:
        return self._to_str()


class NodeMeta(NodeAny):
    """a meta node"""

    def __init__(self,  # type: ignore[no-untyped-def]
                 name: str,
                 attr: Dict[str, Any],
                 parent=None,
                 children=None):
        """build a meta node"""
        super().__init__()  # type: ignore[no-untyped-call]
        self.name = name
        self.type = TYPE_META
        self.attr = attr
        self.parent = parent
        if children:
            self.children = children

    def __str__(self) -> str:
        return self._to_str()
