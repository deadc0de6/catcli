"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

Class for printing nodes
"""

import sys

from catcli.colors import Colors
from catcli.utils import fix_badchars


class NodePrinter:
    """a node printer class"""

    STORAGE = 'storage'
    ARCHIVE = 'archive'
    NBFILES = 'nbfiles'

    @classmethod
    def print_storage_native(cls, pre, name, args, attr):
        """print a storage node"""
        end = ''
        if attr:
            end = f' {Colors.GRAY}({attr}){Colors.RESET}'
        out = f'{pre}{Colors.UND}{cls.STORAGE}{Colors.RESET}:'
        out += ' ' + Colors.PURPLE + fix_badchars(name) + \
            Colors.RESET + end + '\n'
        out += f'  {Colors.GRAY}{args}{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def print_file_native(cls, pre, name, attr):
        """print a file node"""
        nobad = fix_badchars(name)
        out = f'{pre}{nobad}'
        out += f' {Colors.GRAY}[{attr}]{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def print_dir_native(cls, pre, name, depth='', attr=None):
        """print a directory node"""
        end = []
        if depth != '':
            end.append(f'{cls.NBFILES}:{depth}')
        if attr:
            end.append(' '.join([f'{x}:{y}' for x, y in attr]))
        if end:
            endstring = ', '.join(end)
            end = f' [{endstring}]'
        out = pre + Colors.BLUE + fix_badchars(name) + Colors.RESET
        out += f'{Colors.GRAY}{end}{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def print_archive_native(cls, pre, name, archive):
        """archive to stdout"""
        out = pre + Colors.YELLOW + fix_badchars(name) + Colors.RESET
        out += f' {Colors.GRAY}[{cls.ARCHIVE}:{archive}]{Colors.RESET}'
        sys.stdout.write(f'{out}\n')
