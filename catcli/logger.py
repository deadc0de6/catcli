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
            end = ' {}({}){}'.format(Logger.GRAY, attr, Logger.RESET)
        s = '{}{}{}{}:'.format(pre, Logger.UND, Logger.STORAGE, Logger.RESET)
        s += ' {}{}{}{}\n'.format(Logger.PURPLE,
                                  Logger.fix_badchars(name),
                                  Logger.RESET, end)
        s += '  {}{}{}'.format(Logger.GRAY, args, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    def file(pre, name, attr):
        '''print a file node'''
        s = '{}{}'.format(pre, Logger.fix_badchars(name))
        s += ' {}[{}]{}'.format(Logger.GRAY, attr, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    def dir(pre, name, depth='', attr=None):
        '''print a directory node'''
        end = []
        if depth != '':
            end.append('{}:{}'.format(Logger.NBFILES, depth))
        if attr:
            end.append(' '.join(['{}:{}'.format(x, y) for x, y in attr]))
        if end:
            end = ' [{}]'.format(', '.join(end))
        s = '{}{}{}{}'.format(pre, Logger.BLUE,
                              Logger.fix_badchars(name), Logger.RESET)
        s += '{}{}{}'.format(Logger.GRAY, end, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    def arc(pre, name, archive):
        s = '{}{}{}{}'.format(pre, Logger.YELLOW,
                              Logger.fix_badchars(name), Logger.RESET)
        s += ' {}[{}:{}]{}'.format(Logger.GRAY, Logger.ARCHIVE,
                                   archive, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    ######################################################################
    # generic output
    ######################################################################
    def out(string):
        '''to stdout no color'''
        string = Logger.fix_badchars(string)
        sys.stdout.write('{}\n'.format(string))

    def out_err(string):
        '''to stderr no color'''
        string = Logger.fix_badchars(string)
        sys.stderr.write('{}\n'.format(string))

    def debug(string):
        '''to stderr no color'''
        string = Logger.fix_badchars(string)
        sys.stderr.write('[DBG] {}\n'.format(string))

    def info(string):
        '''to stdout in color'''
        string = Logger.fix_badchars(string)
        s = '{}{}{}'.format(Logger.MAGENTA, string, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    def err(string):
        '''to stderr in RED'''
        string = Logger.fix_badchars(string)
        s = '{}{}{}'.format(Logger.RED, string, Logger.RESET)
        sys.stderr.write('{}\n'.format(s))

    def progr(string):
        '''print progress'''
        string = Logger.fix_badchars(string)
        sys.stderr.write('{}\r'.format(string))
        sys.stderr.flush()

    def bold(string):
        '''make it bold'''
        string = Logger.fix_badchars(string)
        return '{}{}{}'.format(Logger.BOLD, string, Logger.RESET)

    def flog(path, string, append=True):
        string = Logger.fix_badchars(string)
        mode = 'w'
        if append:
            mode = 'a'
        with open(path, mode) as f:
            f.write(string)
