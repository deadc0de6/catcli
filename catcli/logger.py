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

    def __init__(self):
        pass

    ######################################################################
    # node specific output
    ######################################################################
    def storage(pre, name, args, attr):
        '''print a storage node'''
        end = ''
        if attr:
            end = ' {}({}){}'.format(Logger.GRAY, attr, Logger.RESET)
        s = '{}{}{}{}:'.format(pre, Logger.UND, Logger.STORAGE, Logger.RESET)
        s += ' {}{}{}{}'.format(Logger.PURPLE, name, Logger.RESET, end)
        s += ' {}{}{}'.format(Logger.GRAY, args, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    def file(pre, name, attr):
        '''print a file node'''
        s = '{}{}'.format(pre, name)
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
        s = '{}{}{}{}'.format(pre, Logger.BLUE, name, Logger.RESET)
        s += '{}{}{}'.format(Logger.GRAY, end, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    def arc(pre, name, archive):
        s = '{}{}{}{}'.format(pre, Logger.YELLOW, name, Logger.RESET)
        s += ' {}[{}:{}]{}'.format(Logger.GRAY, Logger.ARCHIVE,
                                   archive, Logger.RESET)
        sys.stdout.write('{}\n'.format(s))

    ######################################################################
    # generic output
    ######################################################################
    def out(string):
        '''to stdout'''
        sys.stdout.write('{}\n'.format(string))

    def log(string):
        '''to stderr'''
        sys.stderr.write('{}\n'.format(string))

    def info(string):
        '''to stderr in color'''
        s = '{}{}{}'.format(Logger.MAGENTA, string, Logger.RESET)
        sys.stderr.write('{}\n'.format(s))

    def err(string):
        '''to stderr in RED'''
        s = '{}{}{}'.format(Logger.RED, string, Logger.RESET)
        sys.stderr.write('{}\n'.format(s))

    def progr(string):
        '''print progress'''
        sys.stderr.write('{}\r'.format(string))
        sys.stderr.flush()

    def bold(string):
        '''make it bold'''
        return '{}{}{}'.format(Logger.BOLD, string, Logger.RESET)
