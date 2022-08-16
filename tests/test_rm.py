"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for rm
"""

import unittest

from catcli.catcli import cmd_rm, cmd_ls
from catcli.noder import Noder
from catcli.catalog import Catalog
from tests.helpers import clean, get_fakecatalog


class TestRm(unittest.TestCase):

    def test_rm(self):
        # init
        path = 'fake'
        self.addCleanup(clean, path)
        catalog = Catalog(path, force=True, debug=False)
        top = catalog._restore_json(get_fakecatalog())
        noder = Noder()

        # create fake args dict
        args = {'<path>': '', '--recursive': False,
                '--verbose': True,
                '--format': 'native',
                '--raw-size': False}

        # list files and make sure there are children
        args['<path>'] = ''
        found = cmd_ls(args, noder, top)
        self.assertTrue(len(found) > 0)
        self.assertTrue(len(top.children) == 1)

        # rm a not existing storage
        args['<storage>'] = 'abc'
        top = cmd_rm(args, noder, catalog, top)

        # rm a storage
        args['<storage>'] = 'tmpdir'
        top = cmd_rm(args, noder, catalog, top)

        # ensure there no children anymore
        self.assertTrue(len(top.children) == 0)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
