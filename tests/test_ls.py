"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for ls
"""

import unittest

from catcli.catcli import cmd_ls
from catcli.noder import Noder
from catcli.catalog import Catalog
from tests.helpers import get_fakecatalog, clean


class TestWalking(unittest.TestCase):
    """test ls"""

    def test_ls(self):
        """test ls"""
        # init
        path = 'fake'
        self.addCleanup(clean, path)
        catalog = Catalog(path, force=True, debug=False)
        top = catalog._restore_json(get_fakecatalog())
        noder = Noder()

        # create fake args
        args = {'<path>': '', '--recursive': False,
                '--verbose': True,
                '--format': 'native',
                '--raw-size': False}

        # list root
        args['<path>'] = ''
        found = cmd_ls(args, noder, top)
        self.assertTrue(len(found) > 0)

        # list tmpdir that should have 5 children
        args['<path>'] = '/tmpdir'
        found = cmd_ls(args, noder, top)
        self.assertTrue(len(found) == 5)

        # list folder that should have 2 children
        args['<path>'] = '/tmpdir/P4C'
        found = cmd_ls(args, noder, top)
        self.assertTrue(len(found) == 2)

        # list folder that should have 1 children
        args['<path>'] = '/tmpdir/VNN'
        found = cmd_ls(args, noder, top)
        self.assertTrue(len(found) == 1)

        # test not existing path
        args['<path>'] = 'itdoesnotexist'
        found = cmd_ls(args, noder, top)
        self.assertTrue(len(found) == 0)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
