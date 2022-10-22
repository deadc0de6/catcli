"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Logging helper
"""

import sys

# local imports
from catcli.colors import Colors
from catcli.utils import fix_badchars


class Logger:
    """log to stdout/stderr"""

    @classmethod
    def stdout_nocolor(cls, string):
        """to stdout no color"""
        string = fix_badchars(string)
        sys.stdout.write(f'{string}\n')

    @classmethod
    def stderr_nocolor(cls, string):
        """to stderr no color"""
        string = fix_badchars(string)
        sys.stderr.write(f'{string}\n')

    @classmethod
    def debug(cls, string):
        """to stderr no color"""
        cls.stderr_nocolor(f'[DBG] {string}\n')

    @classmethod
    def info(cls, string):
        """to stdout in color"""
        string = fix_badchars(string)
        out = f'{Colors.MAGENTA}{string}{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def err(cls, string):
        """to stderr in RED"""
        string = fix_badchars(string)
        out = f'{Colors.RED}{string}{Colors.RESET}'
        sys.stderr.write(f'{out}\n')

    @classmethod
    def progr(cls, string):
        """print progress"""
        string = fix_badchars(string)
        sys.stderr.write(f'{string}\r')
        sys.stderr.flush()

    @classmethod
    def get_bold_text(cls, string):
        """make it bold"""
        string = fix_badchars(string)
        return f'{Colors.BOLD}{string}{Colors.RESET}'

    @classmethod
    def log_to_file(cls, path, string, append=True):
        """log to file"""
        string = fix_badchars(string)
        mode = 'w'
        if append:
            mode = 'a'
        with open(path, mode, encoding='UTF-8') as file:
            file.write(string)
