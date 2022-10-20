"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for graph
"""

import unittest
import tempfile
import os

from catcli.catcli import cmd_graph
from catcli.noder import Noder
from catcli.catalog import Catalog
from tests.helpers import clean, get_fakecatalog


class TestGraph(unittest.TestCase):
    """test graph"""

    def test_graph(self):
        """test graph"""
        # init
        path = 'fake'
        gpath = tempfile.gettempdir() + os.sep + 'graph.dot'
        self.addCleanup(clean, path)
        self.addCleanup(clean, gpath)
        catalog = Catalog(path, force=True, debug=False)
        top = catalog._restore_json(get_fakecatalog())
        noder = Noder()

        # create fake args dict
        args = {'<path>': gpath, '--verbose': True}

        # create the graph
        cmd_graph(args, noder, top)

        # ensure file exists
        self.assertTrue(os.path.exists(gpath))


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
