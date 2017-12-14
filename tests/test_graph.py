"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for rm
"""

import unittest

from catcli.catcli import *
from catcli.noder import Noder
from catcli.walker import Walker
from catcli.catalog import Catalog
from tests.helpers import *


class TestGraph(unittest.TestCase):

    def test_graph(self):
        # init
        path = 'fake'
        gpath = '/tmp/graph.dot'
        self.addCleanup(clean, path)
        self.addCleanup(clean, gpath)
        catalog = Catalog(path, force=True, verbose=False)
        top = catalog._restore_json(get_fakecatalog())
        noder = Noder()

        # create fake args dict
        args = {'<path>': gpath, '--verbose': True}

        # create the graph
        cmd_graph(args, noder, top)

        # ensure file exists
        self.assertTrue(os.path.exists(gpath))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
