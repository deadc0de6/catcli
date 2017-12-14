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
    UND = '\033[4m'

    def __init__(self):
        pass

    ######################################################################
    # node specific output
    ######################################################################
    def storage(pre, name, attr):
        ''' print a storage node '''
        end = ''
        if attr:
            end = ' {}({}){}'.format(Logger.GRAY, ','.join(attr), Logger.RESET)
        s = '{}{}storage{}:'.format(pre, Logger.UND, Logger.RESET)
        s += ' {}{}{}{}'.format(Logger.PURPLE, name, Logger.RESET, end)
        sys.stdout.write(s+'\n')

    def file(pre, name, attr):
        ''' print a file node '''
        s = '{}{}'.format(pre, name)
        s += ' {}[{}]{}'.format(Logger.GRAY, attr, Logger.RESET)
        sys.stdout.write(s+'\n')

    def dir(pre, name, depth='', attr=None):
        ''' print a directory node '''
        end = []
        if depth != '':
            end.append('nbfiles:{}'.format(depth))
        if attr:
            end.append(' '.join(['{}:{}'.format(x, y) for x, y in attr]))
        if end:
            end = ' [{}]'.format(', '.join(end))
        s = '{}{}{}{}'.format(pre, Logger.BLUE, name, Logger.RESET)
        s += '{}{}{}'.format(Logger.GRAY, end, Logger.RESET)
        sys.stdout.write(s+'\n')

    ######################################################################
    # generic output
    ######################################################################
    def out(string):
        ''' to stdout '''
        sys.stdout.write(string+'\n')

    def log(string):
        ''' to stderr '''
        sys.stderr.write(string+'\n')

    def info(string):
        ''' to stderr in color '''
        s = '{}{}{}'.format(Logger.MAGENTA, string, Logger.RESET)
        sys.stderr.write(s+'\n')

    def err(string):
        ''' to stderr in RED '''
        s = '{}{}{}'.format(Logger.RED, string, Logger.RESET)
        sys.stderr.write(s+'\n')

    def clog(string, color, stdout=True):
        ''' generic printer wrapper for colored text '''
        s = '{}{}{}'.format(color, string, Logger.RESET)
        if stdout:
            sys.stdout.write(s+'\n')
        else:
            sys.stderr.write(s+'\n')

    def progr(string):
        ''' print progress '''
        sys.stderr.write('{}\r'.format(string))
        sys.stderr.flush()

    def get(string, color):
        ''' get color formatted text '''
        return '{}{}{}'.format(color, string, Logger.RESET)
