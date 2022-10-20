"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Catcli filesystem indexer
"""

import os

# local imports
from catcli.logger import Logger


class Walker:
    """a filesystem walker"""

    MAXLINELEN = 80 - 15

    def __init__(self, noder, usehash=True, debug=False,
                 logpath=None):
        """
        @noder: the noder to use
        @hash: calculate hash of nodes
        @debug: debug mode
        @logpath: path where to log catalog changes on reindex
        """
        self.noder = noder
        self.usehash = usehash
        self.noder.set_hashing(self.usehash)
        self.debug = debug
        self.lpath = logpath

    def index(self, path, parent, name, storagepath=''):
        """
        index a directory and store in tree
        @path: path to index
        @parent: parent node
        @name: this stoarge name
        """
        self._debug(f'indexing starting at {path}')
        if not parent:
            parent = self.noder.dir_node(name, path, parent)

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
                node = self.noder.file_node(os.path.basename(file), sub,
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
                dummy = self.noder.dir_node(base, sub, parent, storagepath)
                if not dummy:
                    continue
                cnt += 1
                nstoragepath = os.sep.join([storagepath, base])
                if not storagepath:
                    nstoragepath = base
                _, cnt2 = self.index(sub, dummy, base, nstoragepath)
                cnt += cnt2
            break
        self._progress(None)
        return parent, cnt

    def reindex(self, path, parent, top):
        """reindex a directory and store in tree"""
        cnt = self._reindex(path, parent, top)
        cnt += self.noder.clean_not_flagged(parent)
        return cnt

    def _reindex(self, path, parent, top, storagepath=''):
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
                    self.noder.flag(node)
                    continue
                self._log2file(f'update catalog for \"{sub}\"')
                node = self.noder.file_node(os.path.basename(file), sub,
                                            parent, storagepath)
                self.noder.flag(node)
                cnt += 1
            for adir in dirs:
                self._debug(f'found dir \"{adir}\" under {path}')
                base = os.path.basename(adir)
                sub = os.path.join(root, adir)
                treepath = os.path.join(storagepath, adir)
                reindex, dummy = self._need_reindex(parent, sub, treepath)
                if reindex:
                    self._log2file(f'update catalog for \"{sub}\"')
                    dummy = self.noder.dir_node(base, sub, parent, storagepath)
                    cnt += 1
                self.noder.flag(dummy)
                self._debug(f'reindexing deeper under {sub}')
                nstoragepath = os.sep.join([storagepath, base])
                if not storagepath:
                    nstoragepath = base
                cnt2 = self._reindex(sub, dummy, top, nstoragepath)
                cnt += cnt2
            break
        return cnt

    def _need_reindex(self, top, path, treepath):
        """
        test if node needs re-indexing
        @top: top node (storage)
        @path: abs path to file
        @treepath: rel path from indexed directory
        """
        cnode, changed = self.noder.get_node_if_changed(top, path, treepath)
        if not cnode:
            self._debug(f'\t{path} does not exist')
            return True, cnode
        if cnode and not changed:
            # ignore this node
            self._debug(f'\t{path} has not changed')
            return False, cnode
        if cnode and changed:
            # remove this node and re-add
            self._debug(f'\t{path} has changed')
            self._debug(f'\tremoving node {cnode.name} for {path}')
            cnode.parent = None
        return True, cnode

    def _debug(self, string):
        """print to debug"""
        if not self.debug:
            return
        Logger.debug(string)

    def _progress(self, string):
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

    def _log2file(self, string):
        """log to file"""
        if not self.lpath:
            return
        line = f'{string}\n'
        Logger.flog(self.lpath, line, append=True)
