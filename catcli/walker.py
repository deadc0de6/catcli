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

    def __init__(self, noder, nohash=False):
        self.noder = noder
        self.noder.set_hashing(not nohash)

    def index(self, path, name, parentpath=None, parent=None, isdir=False):
        ''' index a folder and store in tree '''
        if not parent:
            parent = noder.dir_node(name, path, parent)

        cnt = 0
        for (root, dirs, files) in os.walk(path):
            for f in files:
                sub = os.path.join(root, f)
                n = f
                if len(n) > self.MAXLINE:
                    n = f[:self.MAXLINE] + '...'
                Logger.progr('indexing: {:80}'.format(n))
                self.noder.file_node(os.path.basename(f), sub,
                                     parent, parentpath)
                cnt += 1
            for d in dirs:
                base = os.path.basename(d)
                sub = os.path.join(root, d)
                dummy = self.noder.dir_node(base, sub, parent, parentpath)
                _, cnt2 = self.index(sub, base,
                                     parent=dummy, parentpath=parentpath)
                cnt += cnt2
            break
        # clean line
        Logger.progr('{:80}'.format(' '))

        return parent, cnt
