"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

fuse for catcli
"""

import os
import logging
from time import time
from stat import S_IFDIR, S_IFREG
from typing import List, Dict, Any, Optional
import fuse  # type: ignore

# local imports
from catcli.noder import Noder
from catcli.nodes import NodeTop, NodeAny
from catcli import nodes


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
    """fuse filesystem mounter"""

    def __init__(self, mountpoint: str,
                 top: NodeTop,
                 noder: Noder,
                 debug: bool = False):
        """fuse filesystem"""
        filesystem = CatcliFilesystem(top, noder)
        fuse.FUSE(filesystem,
                  mountpoint,
                  foreground=debug,
                  allow_other=True,
                  nothreads=True,
                  debug=debug)


class CatcliFilesystem(fuse.LoggingMixIn, fuse.Operations):  # type: ignore
    """in-memory filesystem for catcli catalog"""

    def __init__(self, top: NodeTop,
                 noder: Noder):
        """init fuse filesystem"""
        self.top = top
        self.noder = noder

    def _get_entry(self, path: str) -> Optional[NodeAny]:
        """return the node pointed by path"""
        pre = f'{SEPARATOR}{nodes.NAME_TOP}'
        if not path.startswith(pre):
            path = pre + path
        found = self.noder.list(self.top, path,
                                rec=False,
                                fmt='native',
                                raw=True)
        if found:
            return found[0]
        return None

    def _get_entries(self, path: str) -> List[NodeAny]:
        """return nodes pointed by path"""
        pre = f'{SEPARATOR}{nodes.NAME_TOP}'
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

    def _getattr(self, path: str) -> Dict[str, Any]:
        entry = self._get_entry(path)
        if not entry:
            return {}

        curt = time()
        mode: Any = S_IFREG
        if isinstance(entry, nodes.NodeArchived):
            mode = S_IFREG
        elif isinstance(entry, nodes.NodeDir):
            mode = S_IFDIR
        elif isinstance(entry, nodes.NodeFile):
            mode = S_IFREG
        elif isinstance(entry, nodes.NodeStorage):
            mode = S_IFDIR
        elif isinstance(entry, nodes.NodeMeta):
            mode = S_IFREG
        elif isinstance(entry, nodes.NodeTop):
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

    def getattr(self, path: str, _fh: Any = None) -> Dict[str, Any]:
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

    def readdir(self, path: str, _fh: Any) -> List[str]:
        """read directory content"""
        logger.info('readdir path: %s', path)
        content = ['.', '..']
        entries = self._get_entries(path)
        for entry in entries:
            content.append(entry.name)
        return content
