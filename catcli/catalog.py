"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Class that represents the catcli catalog
"""

import os
from typing import Optional, List, Dict, Tuple, Union, Any
from anytree.exporter import JsonExporter, DictExporter  # type: ignore
from anytree.importer import JsonImporter  # type: ignore
from anytree import AnyNode  # type: ignore

# local imports
from catcli import nodes
from catcli.nodes import NodeMeta, NodeTop
from catcli.utils import ask
from catcli.logger import Logger


class Catalog:
    """the catalog"""

    def __init__(self, path: str,
                 debug: bool = False,
                 force: bool = False) -> None:
        """
        @path: catalog path
        @usepickle: use pickle
        @debug: debug mode
        @force: force overwrite if exists
        """
        self.path = os.path.expanduser(path)
        self.debug = debug
        self.force = force
        self.metanode: Optional[NodeMeta] = None

    def set_metanode(self, metanode: NodeMeta) -> None:
        """remove the metanode until tree is re-written"""
        self.metanode = metanode
        if self.metanode:
            self.metanode.parent = None

    def exists(self) -> bool:
        """does catalog exist"""
        if not self.path:
            return False
        if os.path.exists(self.path):
            return True
        return False

    def restore(self) -> Optional[NodeTop]:
        """restore the catalog"""
        if not self.path:
            return None
        if not os.path.exists(self.path):
            return None
        with open(self.path, 'r', encoding='UTF-8') as file:
            content = file.read()
        return self._restore_json(content)

    def save(self, node: NodeTop) -> bool:
        """save the catalog"""
        if not self.path:
            Logger.err('Path not defined')
            return False
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        elif os.path.exists(self.path) and not self.force:
            if not ask(f'Update catalog \"{self.path}\"'):
                Logger.info('Catalog not saved')
                return False
        if directory and not os.path.exists(directory):
            Logger.err(f'Cannot write to \"{directory}\"')
            return False
        if self.metanode:
            self.metanode.parent = node
        return self._save_json(node)

    def _debug(self, text: str) -> None:
        if not self.debug:
            return
        Logger.debug(text)

    def _save_json(self, top: NodeTop) -> bool:
        """export the catalog in json"""
        self._debug(f'saving {top} to json...')
        dexporter = DictExporter(attriter=attriter)
        exp = JsonExporter(dictexporter=dexporter, indent=2, sort_keys=True)
        with open(self.path, 'w', encoding='UTF-8') as file:
            exp.write(top, file)
        self._debug(f'Catalog saved to json \"{self.path}\"')
        return True

    def _restore_json(self, string: str) -> Optional[NodeTop]:
        """restore the tree from json"""
        imp = JsonImporter(dictimporter=_DictImporter(debug=self.debug))
        self._debug('import from string...')
        root = imp.import_(string)
        self._debug(f'Catalog imported from json \"{self.path}\"')
        self._debug(f'root imported: {root}')
        if root.type != nodes.TYPE_TOP:
            return None
        top = NodeTop(root.name, children=root.children)
        self._debug(f'top imported: {top}')
        return top


class _DictImporter():

    def __init__(self,
                 nodecls: AnyNode = AnyNode,
                 debug: bool = False):
        self.nodecls = nodecls
        self.debug = debug

    def import_(self, data: Dict[str, str]) -> AnyNode:
        """Import tree from `data`."""
        return self.__import(data)

    def __import(self, data: Union[str, Any],
                 parent: AnyNode = None) -> AnyNode:
        """overwrite parent imoprt"""
        assert isinstance(data, dict)
        assert "parent" not in data
        attrs = dict(data)
        # replace attr
        attrs = back_attriter(attrs, debug=self.debug)
        children: Union[str, Any] = attrs.pop("children", [])
        node = self.nodecls(parent=parent, **attrs)
        for child in children:
            self.__import(child, parent=node)
        return node


def back_attriter(adict: Dict[str, str],
                  debug: bool = False) -> Dict[str, str]:
    """replace attribute on json restore"""
    attrs = {}
    for k, val in adict.items():
        if k == 'size':
            if debug:
                Logger.debug(f'changing {k}={val}')
            k = 'nodesize'
        attrs[k] = val
    return attrs


def attriter(attrs: List[Tuple[str, Any]]) -> List[Tuple[str, Any]]:
    """replace attribute on json save"""
    newattr = []
    for attr in attrs:
        k, val = attr
        if k == 'nodesize':
            k = 'size'
        newattr.append((k, val))
    return newattr
