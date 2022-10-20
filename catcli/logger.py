"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Logging helper
"""

import sys


class Logger:
    """log to stdout/stderr"""

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

    STORAGE = 'storage'
    ARCHIVE = 'archive'
    NBFILES = 'nbfiles'

    @classmethod
    def no_color(cls):
        """disable colors"""
        Logger.RED = ''
        Logger.GREEN = ''
        Logger.YELLOW = ''
        Logger.PURPLE = ''
        Logger.BLUE = ''
        Logger.GRAY = ''
        Logger.MAGENTA = ''
        Logger.RESET = ''
        Logger.EMPH = ''
        Logger.BOLD = ''
        Logger.UND = ''

    @classmethod
    def fix_badchars(cls, line):
        """fix none utf-8 chars in line"""
        return line.encode('utf-8', 'ignore').decode('utf-8')

    ######################################################################
    # node specific output
    ######################################################################
    @classmethod
    def storage(cls, pre, name, args, attr):
        """print a storage node"""
        end = ''
        if attr:
            end = f' {Logger.GRAY}({attr}){Logger.RESET}'
        out = f'{pre}{Logger.UND}{Logger.STORAGE}{Logger.RESET}:'
        out += ' ' + Logger.PURPLE + Logger.fix_badchars(name) + \
            Logger.RESET + end + '\n'
        out += f'  {Logger.GRAY}{args}{Logger.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def file(cls, pre, name, attr):
        """print a file node"""
        nobad = Logger.fix_badchars(name)
        out = f'{pre}{nobad}'
        out += f' {Logger.GRAY}[{attr}]{Logger.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def dir(cls, pre, name, depth='', attr=None):
        """print a directory node"""
        end = []
        if depth != '':
            end.append(f'{Logger.NBFILES}:{depth}')
        if attr:
            end.append(' '.join([f'{x}:{y}' for x, y in attr]))
        if end:
            endstring = ', '.join(end)
            end = f' [{endstring}]'
        out = pre + Logger.BLUE + Logger.fix_badchars(name) + Logger.RESET
        out += f'{Logger.GRAY}{end}{Logger.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def arc(cls, pre, name, archive):
        """archive to stdout"""
        out = pre + Logger.YELLOW + Logger.fix_badchars(name) + Logger.RESET
        out += f' {Logger.GRAY}[{Logger.ARCHIVE}:{archive}]{Logger.RESET}'
        sys.stdout.write(f'{out}\n')

    ######################################################################
    # generic output
    ######################################################################
    @classmethod
    def out(cls, string):
        """to stdout no color"""
        string = Logger.fix_badchars(string)
        sys.stdout.write(f'{string}\n')

    @classmethod
    def out_err(cls, string):
        """to stderr no color"""
        string = Logger.fix_badchars(string)
        sys.stderr.write(f'{string}\n')

    @classmethod
    def debug(cls, string):
        """to stderr no color"""
        string = Logger.fix_badchars(string)
        sys.stderr.write(f'[DBG] {string}\n')

    @classmethod
    def info(cls, string):
        """to stdout in color"""
        string = Logger.fix_badchars(string)
        out = f'{Logger.MAGENTA}{string}{Logger.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def err(cls, string):
        """to stderr in RED"""
        string = Logger.fix_badchars(string)
        out = f'{Logger.RED}{string}{Logger.RESET}'
        sys.stderr.write(f'{out}\n')

    @classmethod
    def progr(cls, string):
        """print progress"""
        string = Logger.fix_badchars(string)
        sys.stderr.write(f'{string}\r')
        sys.stderr.flush()

    @classmethod
    def bold(cls, string):
        """make it bold"""
        string = Logger.fix_badchars(string)
        return f'{Logger.BOLD}{string}{Logger.RESET}'

    @classmethod
    def flog(cls, path, string, append=True):
        """log and fix bad chars"""
        string = Logger.fix_badchars(string)
        mode = 'w'
        if append:
            mode = 'a'
        with open(path, mode, encoding='UTF-8') as file:
            file.write(string)
