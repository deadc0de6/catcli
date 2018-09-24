"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Catcli filesystem indexer
"""

import os
import anytree

# local imports
from catcli.noder import Noder
from catcli.logger import Logger


class Walker:

    MAXLINE = 80 - 15

    def __init__(self, noder, nohash=False, debug=False):
        self.noder = noder
        self.noder.set_hashing(not nohash)
        self.debug = debug

    def index(self, path, parent, name):
        '''index a directory and store in tree'''
        self._debug('indexing starting at {}'.format(path))
        if not parent:
            parent = noder.dir_node(name, path, parent)

        cnt = 0
        for (root, dirs, files) in os.walk(path):
            for f in files:
                self._debug('found file {} under {}'.format(f, path))
                sub = os.path.join(root, f)
                self._log(f)
                self._debug('index file {}'.format(sub))
                self.noder.file_node(os.path.basename(f), sub,
                                     parent, path)
                cnt += 1
            for d in dirs:
                self._debug('found dir {} under {}'.format(d, path))
                base = os.path.basename(d)
                sub = os.path.join(root, d)
                self._debug('index directory {}'.format(sub))
                dummy = self.noder.dir_node(base, sub, parent, path)
                cnt += 1
                _, cnt2 = self.index(sub, dummy, base)
                cnt += cnt2
            break
        self._log(None)
        return parent, cnt

    def reindex(self, path, parent, top):
        '''reindex a directory and store in tree'''
        self._debug('reindexing starting at {}'.format(path))
        cnt = 0
        for (root, dirs, files) in os.walk(path):
            for f in files:
                self._debug('found file {} under {}'.format(f, path))
                sub = os.path.join(root, f)
                maccess = os.path.getmtime(sub)
                reindex, _ = self._need_reindex(parent, f, maccess)
                if not reindex:
                    self._debug('\tignore file {}'.format(sub))
                    continue
                self._debug('\tre-index file {}'.format(sub))
                self._log(f)
                self.noder.file_node(os.path.basename(f), sub,
                                     parent, path)
                cnt += 1
            for d in dirs:
                self._debug('found dir {} under {}'.format(d, path))
                base = os.path.basename(d)
                sub = os.path.join(root, d)
                maccess = os.path.getmtime(sub)
                reindex, dummy = self._need_reindex(parent, base, maccess)
                if reindex:
                    self._debug('\tre-index directory {}'.format(sub))
                    dummy = self.noder.dir_node(base, sub, parent, path)
                self._debug('reindexing deeper under {}'.format(sub))
                cnt2 = self.reindex(sub, dummy, top)
                cnt += cnt2
            break
        self._log(None)
        return cnt

    def _need_reindex(self, top, path, maccess):
        '''test if node needs re-indexing'''
        cnode, newer = self.noder.get_node_if_newer(top, path, maccess)
        if not cnode:
            self._debug('\tdoes not exist')
            return True, cnode
        if cnode and not newer:
            # ignore this node
            self._debug('\tis not newer')
            return False, cnode
        if cnode and newer:
            # remove this node and re-add
            self._debug('\tis newer')
            cnode.parent = None
        self._debug('\tis to be re-indexed')
        return True, cnode

    def _debug(self, string):
        if not self.debug:
            return
        Logger.log(string)

    def _log(self, string):
        if self.debug:
            return
        if not string:
            # clean
            Logger.progr('{:80}'.format(' '))
            return
        if len(string) > self.MAXLINE:
            string = string[:self.MAXLINE] + '...'
        Logger.progr('indexing: {:80}'.format(string))
