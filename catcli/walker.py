"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Catcli filesystem indexer
"""

import os
from typing import Tuple, Optional

# local imports
from catcli.noder import Noder
from catcli.logger import Logger
from catcli.nodes import NodeAny, NodeTop


class Walker:
    """a filesystem walker"""

    MAXLINELEN = 80 - 15

    def __init__(self, noder: Noder,
                 usehash: bool = True,
                 debug: bool = False,
                 logpath: str = ''):
        """
        @noder: the noder to use
        @hash: calculate hash of nodes
        @debug: debug mode
        @logpath: path where to log catalog changes on reindex
        """
        self.noder = noder
        self.usehash = usehash
        self.noder.do_hashing(self.usehash)
        self.debug = debug
        self.lpath = logpath

    def index(self, path: str,
              parent: NodeAny,
              name: str,
              storagepath: str = '') -> Tuple[str, int]:
        """
        index a directory and store in tree
        @path: path to index
        @parent: parent node
        @name: this stoarge name
        """
        self._debug(f'indexing starting at {path}')
        if not parent:
            parent = self.noder.new_dir_node(name, path,
                                             parent, storagepath)

        if os.path.islink(path):
            rel = os.readlink(path)
            abspath = os.path.join(path, rel)
            if os.path.isdir(abspath):
                return parent, 0

        cnt = 0
        for (root, dirs, files) in os.walk(path):
            for file in files:
                self._debug(f'found file {file} under {path}')
                sub = os.path.join(root, file)
                if not os.path.exists(sub):
                    continue
                self._progress(file)
                self._debug(f'index file {sub}')
                node = self.noder.new_file_node(os.path.basename(file), sub,
                                                parent, storagepath)
                if node:
                    cnt += 1
            for adir in dirs:
                self._debug(f'found dir {adir} under {path}')
                base = os.path.basename(adir)
                sub = os.path.join(root, adir)
                self._debug(f'index directory {sub}')
                if not os.path.exists(sub):
                    continue
                dummy = self.noder.new_dir_node(base, sub, parent, storagepath)
                if not dummy:
                    continue
                cnt += 1
                nstoragepath = os.sep.join([storagepath, base])
                if not storagepath:
                    nstoragepath = base
                _, cnt2 = self.index(sub, dummy, base, nstoragepath)
                cnt += cnt2
            break
        self._progress('')
        return parent, cnt

    def reindex(self, path: str, parent: NodeAny, top: NodeTop) -> int:
        """reindex a directory and store in tree"""
        cnt = self._reindex(path, parent, top)
        cnt += self.noder.clean_not_flagged(parent)
        return cnt

    def _reindex(self, path: str,
                 parent: NodeAny,
                 top: NodeTop,
                 storagepath: str = '') -> int:
        """
        reindex a directory and store in tree
        @path: directory path to re-index
        @top: top node (storage)
        @storagepath: rel path relative to indexed directory
        """
        self._debug(f'reindexing starting at {path}')
        cnt = 0
        for (root, dirs, files) in os.walk(path):
            for file in files:
                self._debug(f'found file \"{file}\" under {path}')
                sub = os.path.join(root, file)
                treepath = os.path.join(storagepath, file)
                reindex, node = self._need_reindex(parent, sub, treepath)
                if not reindex:
                    self._debug(f'\tskip file {sub}')
                    if node:
                        node.flag()
                    continue
                node = self.noder.new_file_node(os.path.basename(file), sub,
                                                parent, storagepath)
                if node:
                    node.flag()
                    cnt += 1
            for adir in dirs:
                self._debug(f'found dir \"{adir}\" under {path}')
                base = os.path.basename(adir)
                sub = os.path.join(root, adir)
                treepath = os.path.join(storagepath, adir)
                reindex, dummy = self._need_reindex(parent, sub, treepath)
                if reindex:
                    dummy = self.noder.new_dir_node(base, sub,
                                                    parent, storagepath)
                    cnt += 1
                if dummy:
                    dummy.flag()
                self._debug(f'reindexing deeper under {sub}')
                nstoragepath = os.sep.join([storagepath, base])
                if not storagepath:
                    nstoragepath = base
                if dummy:
                    cnt2 = self._reindex(sub, dummy, top, nstoragepath)
                    cnt += cnt2
            break
        return cnt

    def _need_reindex(self,
                      top: NodeTop,
                      path: str,
                      treepath: str) -> Tuple[bool, Optional[NodeTop]]:
        """
        test if node needs re-indexing
        @top: top node (storage)
        @path: abs path to file
        @treepath: rel path from indexed directory
        """
        node, changed = self.noder.get_node_if_changed(top, path, treepath)
        if not node:
            self._debug(f'\t{path} does not exist')
            return True, node
        if node and not changed:
            # ignore this node
            self._debug(f'\t{path} has not changed')
            return False, node
        if node and changed:
            # remove this node and re-add
            self._debug(f'\t{path} has changed')
            self._debug(f'\tremoving node {node.name} for {path}')
            node.parent = None
        return True, node

    def _debug(self, string: str) -> None:
        """print to debug"""
        if not self.debug:
            return
        Logger.debug(string)

    def _progress(self, string: str) -> None:
        """print progress"""
        if self.debug:
            return
        if not string:
            # clean
            Logger.progr(' ' * 80)
            return
        if len(string) > self.MAXLINELEN:
            string = string[:self.MAXLINELEN] + '...'
        Logger.progr(f'indexing: {string:80}')
