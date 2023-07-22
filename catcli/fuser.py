"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

fuse for catcli
"""

import os
from time import time
from stat import S_IFDIR, S_IFREG
from typing import List, Dict, Any, Optional
try:
    import fuse  # type: ignore
except ModuleNotFoundError:
    pass

# local imports
from catcli.noder import Noder
from catcli.nodes import NodeTop, NodeAny
from catcli.utils import path_to_search_all, path_to_top
from catcli import nodes


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
        path = path_to_top(path)
        found = self.noder.list(self.top, path,
                                rec=False,
                                fmt='native',
                                raw=True)
        if found:
            return found[0]
        return None

    def _get_entries(self, path: str) -> List[NodeAny]:
        """return nodes pointed by path"""
        path = path_to_search_all(path)
        found = self.noder.list(self.top, path,
                                rec=False,
                                fmt='native',
                                raw=True)
        return found

    def _getattr(self, path: str) -> Dict[str, Any]:
        entry = self._get_entry(path)
        if not entry:
            return {}

        maccess = time()
        mode: Any = S_IFREG
        nodesize: int = 0
        if entry.type == nodes.TYPE_ARCHIVED:
            mode = S_IFREG
            nodesize = entry.nodesize
        elif entry.type == nodes.TYPE_DIR:
            mode = S_IFDIR
            nodesize = entry.nodesize
            maccess = entry.maccess
        elif entry.type == nodes.TYPE_FILE:
            mode = S_IFREG
            nodesize = entry.nodesize
            maccess = entry.maccess
        elif entry.type == nodes.TYPE_STORAGE:
            mode = S_IFDIR
            nodesize = entry.nodesize
            maccess = entry.ts
        elif entry.type == nodes.TYPE_META:
            mode = S_IFREG
        elif entry.type == nodes.TYPE_TOP:
            mode = S_IFREG
        mode = mode | 0o777
        return {
            'st_mode': (mode),  # file type
            'st_nlink': 1,  # count hard link
            'st_size': nodesize,
            'st_ctime': maccess,  # attr last modified
            'st_mtime': maccess,  # content last modified
            'st_atime': maccess,  # access time
            'st_uid': os.getuid(),
            'st_gid': os.getgid(),
        }

    def getattr(self, path: str, _fh: Any = None) -> Dict[str, Any]:
        """return attr of file pointed by path"""
        if path == '/':
            # mountpoint
            curt = time()
            meta = {
                'st_mode': (S_IFDIR | 0o777),
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
        content = ['.', '..']
        entries = self._get_entries(path)
        for entry in entries:
            content.append(entry.name)
        return content
