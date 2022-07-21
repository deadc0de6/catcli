"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
"""

import sys

__version__ = '0.8.5'


def main():
    import catcli.catcli
    if catcli.catcli.main():
        sys.exit(0)
    sys.exit(1)
