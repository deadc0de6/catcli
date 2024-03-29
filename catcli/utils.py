"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

helpers
"""

import os
import hashlib
import tempfile
import subprocess
import datetime
import string

# local imports
from catcli.exceptions import CatcliException


WILD = '*'


def md5sum(path: str) -> str:
    """
    calculate md5 sum of a file
    may raise exception
    """
    rpath = os.path.realpath(path)
    if not os.path.exists(rpath):
        raise CatcliException(f'md5sum - file does not exist: {rpath}')
    try:
        with open(rpath, mode='rb') as file:
            hashv = hashlib.md5()
            while True:
                buf = file.read(4096)
                if not buf:
                    break
                hashv.update(buf)
            return hashv.hexdigest()
    except PermissionError:
        pass
    except OSError as exc:
        raise CatcliException(f'md5sum error: {exc}') from exc
    return ''


def size_to_str(size: float,
                raw: bool = True) -> str:
    """convert size to string, optionally human readable"""
    div = 1024.
    suf = ['B', 'K', 'M', 'G', 'T', 'P']
    if raw or size < div:
        return f'{size}'
    for i in suf:
        if size < div:
            return f'{size:.1f}{i}'
        size = size / div
    sufix = suf[-1]
    return f'{size:.1f}{sufix}'


def epoch_to_str(epoch: float) -> str:
    """convert epoch to string"""
    if not epoch:
        return ''
    fmt = '%Y-%m-%d %H:%M:%S'
    timestamp = datetime.datetime.fromtimestamp(epoch)
    return timestamp.strftime(fmt)


def ask(question: str) -> bool:
    """ask the user what to do"""
    resp = input(f'{question} [y|N] ? ')
    return resp.lower() == 'y'


def edit(data: str) -> str:
    """edit the information with the default EDITOR"""
    content = fix_badchars(data)
    editor = os.environ.get('EDITOR', 'vim')
    with tempfile.NamedTemporaryFile(prefix='catcli', suffix='.tmp') as file:
        file.write(content.encode('utf-8'))
        file.flush()
        subprocess.call([editor, file.get_name()])
        file.seek(0)
        new = file.read()
    return new.decode('utf-8')


def fix_badchars(data: str) -> str:
    """fix none utf-8 chars in string"""
    data = "".join(x for x in data if x in string.printable)
    return data.encode("utf-8", "ignore").decode("utf-8")
