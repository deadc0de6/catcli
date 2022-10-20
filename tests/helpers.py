"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Helpers for the unittests
"""

import os
import string
import random
import tempfile
import shutil
import subprocess
import hashlib

TMPSUFFIX = '.catcli'

############################################################
# generic helpers
############################################################


def get_rnd_string(length):
    """Get a random string of specific length """
    alpha = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alpha) for _ in range(length))


def md5sum(path):
    """calculate md5 sum of a file"""
    rpath = os.path.realpath(path)
    if not os.path.exists(rpath):
        return None
    try:
        with open(rpath, mode='rb') as file:
            val = hashlib.md5()
            while True:
                buf = file.read(4096)
                if not buf:
                    break
                val.update(buf)
            return val.hexdigest()
    except PermissionError:
        pass
    return None


def clean(path):
    """Delete file or folder."""
    if not os.path.exists(path):
        return
    if os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def edit_file(path, newcontent):
    """edit file content"""
    return write_to_file(path, newcontent)


def unix_tree(path):
    """print using unix tree tool"""
    if not os.path.exists(path):
        return
    # cmd = ['tree', path]
    cmd = ['ls', '-R', path]
    subprocess.call(cmd)


############################################################
# catcli specific
############################################################


def create_tree():
    """ create a random tree of files and directories """
    dirpath = get_tempdir()
    # create 3 files
    create_rnd_file(dirpath, get_rnd_string(5))
    create_rnd_file(dirpath, get_rnd_string(5))
    create_rnd_file(dirpath, get_rnd_string(5))

    # create 2 directories
    dir1 = create_dir(dirpath, get_rnd_string(3))
    dir2 = create_dir(dirpath, get_rnd_string(3))

    # fill directories
    create_rnd_file(dir1, get_rnd_string(4))
    create_rnd_file(dir1, get_rnd_string(4))
    create_rnd_file(dir2, get_rnd_string(6))

    return dirpath

############################################################
# files and directories
############################################################


def get_tempdir():
    """Get a temporary directory """
    return tempfile.mkdtemp(suffix=TMPSUFFIX)


def create_dir(path, dirname):
    """Create a directory """
    fpath = os.path.join(path, dirname)
    if not os.path.exists(fpath):
        os.mkdir(fpath)
    return fpath


def create_rnd_file(path, filename, content=None):
    """Create the file filename in path with random content if None """
    if not content:
        content = get_rnd_string(100)
    fpath = os.path.join(path, filename)
    return write_to_file(fpath, content)


def write_to_file(path, content):
    """write content to file"""
    with open(path, 'w', encoding='UTF-8') as file:
        file.write(content)
    return path


def read_from_file(path):
    """read file content"""
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='UTF-8') as file:
        content = file.read()
    return content


############################################################
# fake tree in json
############################################################
FAKECATALOG = """
{
  "children": [
    {
      "attr": null,
      "children": [
        {
          "md5": null,
          "name": "7544G",
          "relpath": "tmpj5602ih7.catcli/7544G",
          "size": 100,
          "type": "file"
        },
        {
          "md5": null,
          "name": "KF2ZC",
          "relpath": "tmpj5602ih7.catcli/KF2ZC",
          "size": 100,
          "type": "file"
        },
        {
          "md5": null,
          "name": "Z9OII",
          "relpath": "tmpj5602ih7.catcli/Z9OII",
          "size": 100,
          "type": "file"
        },
        {
          "children": [
            {
              "md5": null,
              "name": "M592O9",
              "relpath": "tmpj5602ih7.catcli/VNN/M592O9",
              "size": 100,
              "type": "file"
            }
          ],
          "md5": null,
          "name": "VNN",
          "relpath": "VNN",
          "size": 100,
          "type": "dir"
        },
        {
          "children": [
            {
              "md5": null,
              "name": "X37H",
              "relpath": "tmpj5602ih7.catcli/P4C/X37H",
              "size": 100,
              "type": "file"
            },
            {
              "md5": null,
              "name": "I566",
              "relpath": "tmpj5602ih7.catcli/P4C/I566",
              "size": 100,
              "type": "file"
            }
          ],
          "md5": null,
          "name": "P4C",
          "relpath": "P4C",
          "size": 200,
          "type": "dir"
        }
      ],
      "free": 100000000000,
      "name": "tmpdir",
      "size": 0,
      "total": 200000000000,
      "ts": 1500000000.0000000,
      "type": "storage"
    }
  ],
  "name": "top",
  "type": "top"
}
"""


def get_fakecatalog():
    """catalog constructed through test_index"""
    return FAKECATALOG
