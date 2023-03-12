"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Catcli generic compressed data lister
"""

import os
import tarfile
import zipfile
from typing import List


class Decomp:
    """decompressor"""

    def __init__(self) -> None:
        self.ext = {
            'tar': self._tar,
            'tgz': self._tar,
            'gz': self._tar,
            'tar.gz': self._tar,
            'xz': self._tar,
            'tar.xz': self._tar,
            'lzma': self._tar,
            'tar.lzma': self._tar,
            'tlz': self._tar,
            'bz2': self._tar,
            'tar.bz2': self._tar,
            'zip': self._zip}

    def get_formats(self) -> List[str]:
        """return list of supported extensions"""
        return list(self.ext.keys())

    def get_names(self, path: str) -> List[str]:
        """get tree of compressed archive"""
        ext = os.path.splitext(path)[1][1:].lower()
        if ext in list(self.ext):
            return self.ext[ext](path)
        return []

    @staticmethod
    def _tar(path: str) -> List[str]:
        """return list of file names in tar"""
        if not tarfile.is_tarfile(path):
            return []
        with tarfile.open(path, "r") as tar:
            return tar.getnames()

    @staticmethod
    def _zip(path: str) -> List[str]:
        """return list of file names in zip"""
        if not zipfile.is_zipfile(path):
            return []
        with zipfile.ZipFile(path) as file:
            return file.namelist()
