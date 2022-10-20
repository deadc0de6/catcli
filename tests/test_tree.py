"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for tree
"""

import unittest

from catcli.catcli import cmd_tree
from catcli.noder import Noder
from catcli.catalog import Catalog
from tests.helpers import clean, get_fakecatalog


class TestTree(unittest.TestCase):
    """Test the tree"""

    def test_tree(self):
        """test the tree"""
        # init
        path = 'fake'
        self.addCleanup(clean, path)
        catalog = Catalog(path, force=True, debug=False)
        top = catalog._restore_json(get_fakecatalog())
        noder = Noder()

        # create fake args dict
        args = {
            '<path>': path,
            '--verbose': True,
            '--format': 'native',
            '--header': False,
            '--raw-size': False,
        }

        # print tree and wait for any errors
        cmd_tree(args, noder, top)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
