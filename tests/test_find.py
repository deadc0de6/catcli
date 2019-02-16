"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for find
"""

import unittest

import catcli

from catcli.catcli import *
from catcli.noder import Noder
from catcli.walker import Walker
from catcli.catalog import Catalog
from catcli.logger import Logger
from catcli.utils import *
from tests.helpers import *


class TestFind(unittest.TestCase):

    def test_find(self):
        # init
        catalog = Catalog('fake', force=True, verbose=False)
        top = catalog._restore_json(get_fakecatalog())
        noder = Noder()

        # create fake args
        args = {'<term>': '7544G', '--script': True,
                '--verbose': True, '--parent': False,
                '--directory': False, '--path': None}

        # try to find something
        found = cmd_find(args, noder, top)
        self.assertTrue(len(found) > 0)

        # try to find something that does not exist
        args['<term>'] = 'verynotfoundnote'
        found = cmd_find(args, noder, top)
        self.assertTrue(len(found) == 0)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
