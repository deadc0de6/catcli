"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for indexing
"""

import os
import unittest

from catcli.catcli import cmd_index
from catcli.noder import Noder
from catcli.catalog import Catalog
from tests.helpers import get_tempdir, create_rnd_file, clean, \
        get_rnd_string, create_dir


class TestIndexing(unittest.TestCase):

    def test_index(self):
        # init
        workingdir = get_tempdir()
        catalogpath = create_rnd_file(workingdir, 'catalog.json', content='')
        self.addCleanup(clean, workingdir)

        dirpath = get_tempdir()
        self.addCleanup(clean, dirpath)

        # create 3 files
        f1 = create_rnd_file(dirpath, get_rnd_string(5))
        f2 = create_rnd_file(dirpath, get_rnd_string(5))
        f3 = create_rnd_file(dirpath, get_rnd_string(5))

        # create 2 directories
        d1 = create_dir(dirpath, get_rnd_string(3))
        d2 = create_dir(dirpath, get_rnd_string(3))

        # fill directories with files
        _ = create_rnd_file(d1, get_rnd_string(4))
        _ = create_rnd_file(d1, get_rnd_string(4))
        _ = create_rnd_file(d2, get_rnd_string(6))

        noder = Noder()
        top = noder.new_top_node()
        catalog = Catalog(catalogpath, force=True, verbose=False)

        # create fake args
        tmpdirname = 'tmpdir'
        args = {'<path>': dirpath, '<name>': tmpdirname,
                '--hash': True, '--meta': ['some meta'],
                '--no-subsize': False, '--verbose': True}

        # index the directory
        cmd_index(args, noder, catalog, top)
        self.assertTrue(os.stat(catalogpath).st_size != 0)

        # explore the top node to find all nodes
        self.assertTrue(len(top.children) == 1)
        storage = top.children[0]
        self.assertTrue(len(storage.children) == 5)

        # ensures files and directories are in
        names = [x.name for x in storage.children]
        self.assertTrue(os.path.basename(f1) in names)
        self.assertTrue(os.path.basename(f2) in names)
        self.assertTrue(os.path.basename(f3) in names)
        self.assertTrue(os.path.basename(d1) in names)
        self.assertTrue(os.path.basename(d2) in names)

        for node in storage.children:
            if node.name == os.path.basename(d1):
                self.assertTrue(len(node.children) == 2)
            elif node.name == os.path.basename(d2):
                self.assertTrue(len(node.children) == 1)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
