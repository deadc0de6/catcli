"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
"""

# pylint: disable=C0415
import sys


def main() -> None:
    """entry point"""
    import catcli.catcli
    if catcli.catcli.main():
        sys.exit(0)
    sys.exit(1)
