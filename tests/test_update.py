"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for updating an index
"""

import unittest
import os
import anytree

from catcli.catcli import cmd_index, cmd_update
from catcli.noder import Noder
from catcli.catalog import Catalog
from tests.helpers import create_dir, create_rnd_file, get_tempdir, \
        clean, unix_tree, edit_file, read_from_file, md5sum


class TestUpdate(unittest.TestCase):
    """test update"""

    def test_update(self):
        """test update"""
        # init
        workingdir = get_tempdir()
        catalogpath = create_rnd_file(workingdir, 'catalog.json', content='')
        self.addCleanup(clean, workingdir)

        dirpath = get_tempdir()
        self.addCleanup(clean, dirpath)

        # create 3 files
        file1 = create_rnd_file(dirpath, 'file1')
        file2 = create_rnd_file(dirpath, 'file2')
        file3 = create_rnd_file(dirpath, 'file3')
        file4 = create_rnd_file(dirpath, 'file4')

        # create 2 directories
        dir1 = create_dir(dirpath, 'dir1')
        dir2 = create_dir(dirpath, 'dir2')

        # fill directories with files
        d1f1 = create_rnd_file(dir1, 'dir1file1')
        d1f2 = create_rnd_file(dir1, 'dir1file2')
        d2f1 = create_rnd_file(dir2, 'dir2file1')
        d2f2 = create_rnd_file(dir2, 'dir2file2')

        noder = Noder(debug=True)
        noder.do_hashing(True)
        top = noder.new_top_node()
        catalog = Catalog(catalogpath, force=True, debug=False)

        # get checksums
        f4_md5 = md5sum(file4)
        self.assertTrue(f4_md5)
        d1f1_md5 = md5sum(d1f1)
        self.assertTrue(d1f1_md5)
        d2f2_md5 = md5sum(d2f2)
        self.assertTrue(d2f2_md5)

        # create fake args
        tmpdirname = 'tmpdir'
        args = {'<path>': dirpath, '<name>': tmpdirname,
                '--hash': True, '--meta': ['some meta'],
                '--verbose': True, '--lpath': None}

        # index the directory
        unix_tree(dirpath)
        cmd_index(args, noder, catalog, top)
        self.assertTrue(os.stat(catalogpath).st_size != 0)

        # ensure md5 sum are in
        nods = noder.find(top, os.path.basename(file4))
        self.assertEqual(len(nods), 1)
        nod = nods[0]
        self.assertTrue(nod)
        self.assertEqual(nod.md5, f4_md5)

        # print catalog
        noder.print_tree(top)

        # add some files and directories
        new1 = create_rnd_file(dir1, 'newf1')
        new2 = create_rnd_file(dirpath, 'newf2')
        new3 = create_dir(dirpath, 'newd3')
        new4 = create_dir(dir2, 'newd4')
        new5 = create_rnd_file(new4, 'newf5')
        unix_tree(dirpath)

        # modify files
        editval = 'edited'
        edit_file(d1f1, editval)
        d1f1_md5_new = md5sum(d1f1)
        self.assertTrue(d1f1_md5_new)
        self.assertTrue(d1f1_md5_new != d1f1_md5)

        # change file without mtime
        maccess = os.path.getmtime(file4)
        editval = 'edited'
        edit_file(file4, editval)
        # reset edit time
        os.utime(file4, (maccess, maccess))
        f4_md5_new = md5sum(d1f1)
        self.assertTrue(f4_md5_new)
        self.assertTrue(f4_md5_new != f4_md5)

        # change file without mtime
        maccess = os.path.getmtime(d2f2)
        editval = 'edited'
        edit_file(d2f2, editval)
        # reset edit time
        os.utime(d2f2, (maccess, maccess))
        d2f2_md5_new = md5sum(d2f2)
        self.assertTrue(d2f2_md5_new)
        self.assertTrue(d2f2_md5_new != d2f2_md5)

        # update storage
        cmd_update(args, noder, catalog, top)

        # print catalog
        # print(read_from_file(catalogpath))
        noder.print_tree(top)

        # explore the top node to find all nodes
        self.assertEqual(len(top.children), 1)
        storage = top.children[0]
        self.assertEqual(len(storage.children), 8)

        # ensure d1f1 md5 sum has changed in catalog
        nods = noder.find(top, os.path.basename(d1f1))
        self.assertTrue(len(nods) == 1)
        nod = nods[0]
        self.assertTrue(nod)
        self.assertTrue(nod.md5 != d1f1_md5)
        self.assertTrue(nod.md5 == d1f1_md5_new)

        # ensure f4 md5 sum has changed in catalog
        nods = noder.find(top, os.path.basename(file4))
        self.assertTrue(len(nods) == 1)
        nod = nods[0]
        self.assertTrue(nod)
        self.assertTrue(nod.md5 != f4_md5)
        self.assertTrue(nod.md5 == f4_md5_new)

        # ensure d2f2 md5 sum has changed in catalog
        nods = noder.find(top, os.path.basename(d2f2))
        self.assertTrue(len(nods) == 1)
        nod = nods[0]
        self.assertTrue(nod)
        self.assertTrue(nod.md5 != d2f2_md5)
        self.assertTrue(nod.md5 == d2f2_md5_new)

        # ensures files and directories are in
        names = [node.get_name() for node in anytree.PreOrderIter(storage)]
        print(names)
        self.assertTrue(os.path.basename(file1) in names)
        self.assertTrue(os.path.basename(file2) in names)
        self.assertTrue(os.path.basename(file3) in names)
        self.assertTrue(os.path.basename(file4) in names)
        self.assertTrue(os.path.basename(dir1) in names)
        self.assertTrue(os.path.basename(d1f1) in names)
        self.assertTrue(os.path.basename(d1f2) in names)
        self.assertTrue(os.path.basename(dir2) in names)
        self.assertTrue(os.path.basename(d2f1) in names)
        self.assertTrue(os.path.basename(new1) in names)
        self.assertTrue(os.path.basename(new2) in names)
        self.assertTrue(os.path.basename(new3) in names)
        self.assertTrue(os.path.basename(new4) in names)
        self.assertTrue(os.path.basename(new5) in names)

        for node in storage.children:
            if node.get_name() == os.path.basename(dir1):
                self.assertTrue(len(node.children) == 3)
            elif node.get_name() == os.path.basename(dir2):
                self.assertTrue(len(node.children) == 3)
            elif node.get_name() == os.path.basename(new3):
                self.assertTrue(len(node.children) == 0)
            elif node.get_name() == os.path.basename(new4):
                self.assertTrue(len(node.children) == 1)
        self.assertTrue(read_from_file(d1f1) == editval)

        # remove some files
        clean(d1f1)
        clean(dir2)
        clean(new2)
        clean(new4)

        # update storage
        cmd_update(args, noder, catalog, top)

        # ensures files and directories are (not) in
        names = [node.get_name() for node in anytree.PreOrderIter(storage)]
        print(names)
        self.assertTrue(os.path.basename(file1) in names)
        self.assertTrue(os.path.basename(file2) in names)
        self.assertTrue(os.path.basename(file3) in names)
        self.assertTrue(os.path.basename(file4) in names)
        self.assertTrue(os.path.basename(dir1) in names)
        self.assertTrue(os.path.basename(d1f1) not in names)
        self.assertTrue(os.path.basename(d1f2) in names)
        self.assertTrue(os.path.basename(dir2) not in names)
        self.assertTrue(os.path.basename(d2f1) not in names)
        self.assertTrue(os.path.basename(d2f1) not in names)
        self.assertTrue(os.path.basename(new1) in names)
        self.assertTrue(os.path.basename(new2) not in names)
        self.assertTrue(os.path.basename(new3) in names)
        self.assertTrue(os.path.basename(new4) not in names)
        self.assertTrue(os.path.basename(new5) not in names)
        for node in storage.children:
            if node.get_name() == os.path.basename(dir1):
                self.assertTrue(len(node.children) == 2)
            elif node.get_name() == os.path.basename(new3):
                self.assertTrue(len(node.children) == 0)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
