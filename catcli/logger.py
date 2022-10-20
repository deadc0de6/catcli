"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Logging helper
"""

import sys


class Logger:

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

    def no_color():
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

    def fix_badchars(line):
        return line.encode('utf-8', 'ignore').decode('utf-8')

    ######################################################################
    # node specific output
    ######################################################################
    def storage(pre, name, args, attr):
        '''print a storage node'''
        end = ''
        if attr:
            end = f' {Logger.GRAY}({attr}){Logger.RESET}'
        s = f'{pre}{Logger.UND}{Logger.STORAGE}{Logger.RESET}:'
        s += ' ' + Logger.PURPLE + Logger.fix_badchars(name) + \
            Logger.RESET + end + '\n'
        s += f'  {Logger.GRAY}{args}{Logger.RESET}'
        sys.stdout.write(f'{s}\n')

    def file(pre, name, attr):
        '''print a file node'''
        nobad = Logger.fix_badchars(name)
        s = f'{pre}{nobad}'
        s += f' {Logger.GRAY}[{attr}]{Logger.RESET}'
        sys.stdout.write(f'{s}\n')

    def dir(pre, name, depth='', attr=None):
        '''print a directory node'''
        end = []
        if depth != '':
            end.append(f'{Logger.NBFILES}:{depth}')
        if attr:
            end.append(' '.join([f'{x}:{y}' for x, y in attr]))
        if end:
            endstring = ', '.join(end)
            end = f' [{endstring}]'
        s = pre + Logger.BLUE + Logger.fix_badchars(name) + Logger.RESET
        s += f'{Logger.GRAY}{end}{Logger.RESET}'
        sys.stdout.write(f'{s}\n')

    def arc(pre, name, archive):
        s = pre + Logger.YELLOW + Logger.fix_badchars(name) + Logger.RESET
        s += f' {Logger.GRAY}[{Logger.ARCHIVE}:{archive}]{Logger.RESET}'
        sys.stdout.write(f'{s}\n')

    ######################################################################
    # generic output
    ######################################################################
    def out(string):
        '''to stdout no color'''
        string = Logger.fix_badchars(string)
        sys.stdout.write(f'{string}\n')

    def out_err(string):
        '''to stderr no color'''
        string = Logger.fix_badchars(string)
        sys.stderr.write(f'{string}\n')

    def debug(string):
        '''to stderr no color'''
        string = Logger.fix_badchars(string)
        sys.stderr.write(f'[DBG] {string}\n')

    def info(string):
        '''to stdout in color'''
        string = Logger.fix_badchars(string)
        s = f'{Logger.MAGENTA}{string}{Logger.RESET}'
        sys.stdout.write(f'{s}\n')

    def err(string):
        '''to stderr in RED'''
        string = Logger.fix_badchars(string)
        s = f'{Logger.RED}{string}{Logger.RESET}'
        sys.stderr.write(f'{s}\n')

    def progr(string):
        '''print progress'''
        string = Logger.fix_badchars(string)
        sys.stderr.write(f'{string}\r')
        sys.stderr.flush()

    def bold(string):
        '''make it bold'''
        string = Logger.fix_badchars(string)
        return f'{Logger.BOLD}{string}{Logger.RESET}'

    def flog(path, string, append=True):
        string = Logger.fix_badchars(string)
        mode = 'w'
        if append:
            mode = 'a'
        with open(path, mode) as f:
            f.write(string)
