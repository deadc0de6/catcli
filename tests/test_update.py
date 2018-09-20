"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for updating an index
"""

import unittest

from catcli.catcli import *
from catcli.noder import Noder
from catcli.walker import Walker
from catcli.catalog import Catalog
from tests.helpers import *


class TestIndexing(unittest.TestCase):

    def test_index(self):
        # init
        workingdir = get_tempdir()
        catalogpath = create_rnd_file(workingdir, 'catalog.json', content='')
        self.addCleanup(clean, workingdir)

        dirpath = get_tempdir()
        self.addCleanup(clean, dirpath)

        # create 3 files
        f1 = create_rnd_file(dirpath, 'file1')
        f2 = create_rnd_file(dirpath, 'file2')
        f3 = create_rnd_file(dirpath, 'file3')

        # create 2 directories
        d1 = create_dir(dirpath, 'dir1')
        d2 = create_dir(dirpath, 'dir2')

        # fill directories with files
        d1f1 = create_rnd_file(d1, 'dir1file1')
        d1f2 = create_rnd_file(d1, 'dir1file2')
        d2f1 = create_rnd_file(d2, 'dir2file1')

        noder = Noder()
        top = noder.new_top_node()
        walker = Walker(noder)
        catalog = Catalog(catalogpath, force=True, verbose=False)

        # create fake args
        tmpdirname = 'tmpdir'
        args = {'<path>': dirpath, '<name>': tmpdirname,
                '--hash': True, '--meta': 'some meta',
                '--subsize': True, '--verbose': True}

        # index the directory
        unix_tree(dirpath)
        cmd_index(args, noder, catalog, top, debug=True)
        self.assertTrue(os.stat(catalogpath).st_size != 0)

        # print catalog
        noder.print_tree(top)

        # add some files and directories
        new1 = create_rnd_file(d1, 'newf1')
        new2 = create_rnd_file(dirpath, 'newf2')
        new3 = create_dir(dirpath, 'newd3')
        new4 = create_dir(d2, 'newd4')
        new5 = create_rnd_file(new4, 'newf5')
        unix_tree(dirpath)

        # modify files
        EDIT = 'edited'
        edit_file(d1f1, EDIT)

        # update storage
        cmd_update(args, noder, catalog, top, debug=True)

        # print catalog
        # print(read_from_file(catalogpath))
        noder.print_tree(top)

        # explore the top node to find all nodes
        self.assertTrue(len(top.children) == 1)
        storage = top.children[0]
        self.assertTrue(len(storage.children) == 7)

        # ensures files and directories are in
        names = [x.name for x in storage.children]
        self.assertTrue(os.path.basename(f1) in names)
        self.assertTrue(os.path.basename(f2) in names)
        self.assertTrue(os.path.basename(f3) in names)
        self.assertTrue(os.path.basename(d1) in names)
        self.assertTrue(os.path.basename(d2) in names)
        self.assertTrue(os.path.basename(new3) in names)
        self.assertTrue(os.path.basename(new2) in names)

        for node in storage.children:
            if node.name == os.path.basename(d1):
                self.assertTrue(len(node.children) == 3)
            elif node.name == os.path.basename(d2):
                self.assertTrue(len(node.children) == 2)
            elif node.name == os.path.basename(new3):
                self.assertTrue(len(node.children) == 0)
            elif node.name == os.path.basename(new4):
                self.assertTrue(len(node.children) == 1)
        self.assertTrue(read_from_file(d1f1) == EDIT)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
