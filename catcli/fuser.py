"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

fuse for catcli
"""

import os
import logging
from time import time
from stat import S_IFDIR, S_IFREG
import fuse
from .noder import Noder


# build custom logger to log in /tmp
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/tmp/fuse-catcli.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# globals
WILD = '*'
SEPARATOR = '/'


class Fuser:
    """fuser filesystem"""

    def __init__(self, mountpoint, top, noder):
        """fuse filesystem"""
        filesystem = CatcliFilesystem(top, noder)
        fuse.FUSE(filesystem,
                  mountpoint,
                  foreground=True,
                  allow_other=True,
                  nothreads=True,
                  debug=True)


class CatcliFilesystem(fuse.LoggingMixIn, fuse.Operations):
    """in-memory filesystem for catcli catalog"""

    def __init__(self, top, noder):
        """init fuse filesystem"""
        self.top = top
        self.noder = noder

    def _get_entry(self, path):
        pre = f'{SEPARATOR}{self.noder.NAME_TOP}'
        if not path.startswith(pre):
            path = pre + path
        found = self.noder.list(self.top, path,
                                rec=False,
                                fmt='native',
                                raw=True)
        if found:
            return found[0]
        return []

    def _get_entries(self, path):
        pre = f'{SEPARATOR}{self.noder.NAME_TOP}'
        if not path.startswith(pre):
            path = pre + path
        if not path.endswith(SEPARATOR):
            path += SEPARATOR
        if not path.endswith(WILD):
            path += WILD
        found = self.noder.list(self.top, path,
                                rec=False,
                                fmt='native',
                                raw=True)
        return found

    def _getattr(self, path):
        entry = self._get_entry(path)
        if not entry:
            return None

        curt = time()
        mode = S_IFREG
        if entry.type == Noder.TYPE_ARC:
            mode = S_IFREG
        elif entry.type == Noder.TYPE_DIR:
            mode = S_IFDIR
        elif entry.type == Noder.TYPE_FILE:
            mode = S_IFREG
        elif entry.type == Noder.TYPE_STORAGE:
            mode = S_IFDIR
        elif entry.type == Noder.TYPE_META:
            mode = S_IFREG
        elif entry.type == Noder.TYPE_TOP:
            mode = S_IFREG
        return {
            'st_mode': (mode),
            'st_nlink': 1,
            'st_size': 0,
            'st_ctime': curt,
            'st_mtime': curt,
            'st_atime': curt,
            'st_uid': os.getuid(),
            'st_gid': os.getgid(),
        }

    def getattr(self, path, _fh=None):
        """return attr of file pointed by path"""
        logger.info('getattr path: %s', path)

        if path == '/':
            # mountpoint
            curt = time()
            meta = {
                'st_mode': (S_IFDIR),
                'st_nlink': 1,
                'st_size': 0,
                'st_ctime': curt,
                'st_mtime': curt,
                'st_atime': curt,
                'st_uid': os.getuid(),
                'st_gid': os.getgid(),
            }
            return meta
        meta = self._getattr(path)
        return meta

    def readdir(self, path, _fh):
        """read directory content"""
        logger.info('readdir path: %s', path)
        content = ['.', '..']
        entries = self._get_entries(path)
        for entry in entries:
            content.append(entry.name)
        return content
