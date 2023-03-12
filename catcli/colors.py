"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

shell colors
"""

from typing import TypeVar, Type


CLASSTYPE = TypeVar('CLASSTYPE', bound='Colors')


class Colors:
    """shell colors"""

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[1;35m'
    BLUE = '\033[94m'
    GRAY = '\033[0;37m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    EMPH = '\033[33m'
    BOLD = '\033[1m'
    UND = '\033[4m'

    @classmethod
    def no_color(cls: Type[CLASSTYPE]) -> None:
        """disable colors"""
        Colors.RED = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.PURPLE = ''
        Colors.BLUE = ''
        Colors.GRAY = ''
        Colors.MAGENTA = ''
        Colors.RESET = ''
        Colors.EMPH = ''
        Colors.BOLD = ''
        Colors.UND = ''
