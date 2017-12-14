"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

helpers
"""

import os
import hashlib

# local imports
from catcli.logger import Logger


def md5sum(path):
    ''' calculate md5 sum of a file '''
    p = os.path.realpath(path)
    if not os.path.exists(p):
        Logger.err('\nunable to get md5sum on {}'.format(path))
        return None
    try:
        with open(p, mode='rb') as f:
            d = hashlib.md5()
            while True:
                buf = f.read(4096)
                if not buf:
                    break
                d.update(buf)
            return d.hexdigest()
    except PermissionError:
        pass
    return None


def human(size):
    ''' human readable size '''
    div = 1024.
    suf = ['B', 'K', 'M', 'G', 'T', 'P']
    if size < div:
        return '{}'.format(size)
    for i in suf:
        if size < div:
            return '{:.1f}{}'.format(size, i)
        size = size / div
    return '{:.1f}{}'.format(size, suf[-1])


def ask(question):
    ''' ask the user what to do '''
    resp = input('{} [y|N] ? '.format(question))
    return resp.lower() == 'y'
