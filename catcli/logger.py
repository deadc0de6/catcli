"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Logging helper
"""

import sys
from typing import TypeVar, Type

# local imports
from catcli.colors import Colors
from catcli.utils import fix_badchars


CLASSTYPE = TypeVar('CLASSTYPE', bound='Logger')


class Logger:
    """log to stdout/stderr"""

    @classmethod
    def stdout_nocolor(cls: Type[CLASSTYPE],
                       string: str) -> None:
        """to stdout no color"""
        string = fix_badchars(string)
        sys.stdout.write(f'{string}\n')

    @classmethod
    def stderr_nocolor(cls: Type[CLASSTYPE],
                       string: str) -> None:
        """to stderr no color"""
        string = fix_badchars(string)
        sys.stderr.write(f'{string}\n')

    @classmethod
    def debug(cls: Type[CLASSTYPE],
              string: str) -> None:
        """to stderr no color"""
        cls.stderr_nocolor(f'[DBG] {string}')

    @classmethod
    def info(cls: Type[CLASSTYPE],
             string: str) -> None:
        """to stdout in color"""
        string = fix_badchars(string)
        out = f'{Colors.MAGENTA}{string}{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def err(cls: Type[CLASSTYPE],
            string: str) -> None:
        """to stderr in RED"""
        string = fix_badchars(string)
        out = f'{Colors.RED}{string}{Colors.RESET}'
        sys.stderr.write(f'{out}\n')

    @classmethod
    def progr(cls: Type[CLASSTYPE],
              string: str) -> None:
        """print progress"""
        string = fix_badchars(string)
        sys.stderr.write(f'{string}\r')
        sys.stderr.flush()

    @classmethod
    def get_bold_text(cls: Type[CLASSTYPE],
                      string: str) -> str:
        """make it bold"""
        string = fix_badchars(string)
        return f'{Colors.BOLD}{string}{Colors.RESET}'
