"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Basic unittest for ls
"""

import unittest

from catcli.decomp import Decomp


class TestDecomp(unittest.TestCase):
    """test ls"""

    def test_list(self):
        """test decomp formats"""
        dec = Decomp()
        formats = dec.get_formats()
        self.assertTrue('zip' in formats)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
