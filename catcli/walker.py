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

    def index(self, path, name, parent):
        return self._index(path, name, parent)

    def reindex(self, path, parent, top):
        '''reindex a directory and store in tree'''
        cnt = 0
        for (root, dirs, files) in os.walk(path):
            for f in files:
                sub = os.path.join(root, f)
                if not self._need_reindex(top, sub):
                    self._debug('ignore {}'.format(sub))
                    continue
                self._debug('re-index {}'.format(sub))
                self._log(f)
                self.noder.file_node(os.path.basename(f), sub,
                                     parent, path)
                cnt += 1
            for d in dirs:
                base = os.path.basename(d)
                sub = os.path.join(root, d)
                if not self._need_reindex(top, sub):
                    self._debug('ignore {}'.format(sub))
                    continue
                self._debug('re-index {}'.format(sub))
                dummy = self.noder.dir_node(base, sub, parent, path)
                cnt2 = self.reindex(sub, dummy, top)
                cnt += cnt2
            break
        self._log(None)
        return cnt

    def _index(self, path, name, parent):
        '''index a directory and store in tree'''
        if not parent:
            parent = noder.dir_node(name, path, parent)

        cnt = 0
        for (root, dirs, files) in os.walk(path):
            for f in files:
                sub = os.path.join(root, f)
                self._log(f)
                self.noder.file_node(os.path.basename(f), sub,
                                     parent, path)
                cnt += 1
            for d in dirs:
                base = os.path.basename(d)
                sub = os.path.join(root, d)
                dummy = self.noder.dir_node(base, sub, parent, path)
                _, cnt2 = self._index(sub, base, dummy)
                cnt += cnt2
            break
        self._log(None)
        return parent, cnt

    def _need_reindex(self, top, path):
        '''test if node needs re-indexing'''
        cnode, newer = self.noder.get_node_if_newer(top, path)
        if cnode and not newer:
            # ignore this node
            return False
        if cnode and newer:
            # remove this node and re-add
            cnode.parent = None
        return True

    def _debug(self, string):
        if not self.debug:
            return
        Logger.info(string)

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
