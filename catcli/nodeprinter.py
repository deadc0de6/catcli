"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

Class for printing nodes
"""

import sys
from typing import TypeVar, Type, Optional, Tuple, List, \
    Dict, Any

from catcli.colors import Colors
from catcli.utils import fix_badchars


CLASSTYPE = TypeVar('CLASSTYPE', bound='NodePrinter')


class NodePrinter:
    """a node printer class"""

    STORAGE = 'storage'
    ARCHIVE = 'archive'
    NBFILES = 'nbfiles'

    @classmethod
    def print_storage_native(cls: Type[CLASSTYPE], pre: str,
                             name: str, args: str,
                             attr: Dict[str, Any]) -> None:
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
    def print_file_native(cls: Type[CLASSTYPE], pre: str,
                          name: str, attr: str) -> None:
        """print a file node"""
        nobad = fix_badchars(name)
        out = f'{pre}{nobad}'
        out += f' {Colors.GRAY}[{attr}]{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def print_dir_native(cls: Type[CLASSTYPE], pre: str,
                         name: str,
                         depth: int = 0,
                         attr: Optional[List[Tuple[str, str]]] = None) -> None:
        """print a directory node"""
        end = []
        if depth > 0:
            end.append(f'{cls.NBFILES}:{depth}')
        if attr:
            end.append(' '.join([f'{x}:{y}' for x, y in attr]))
        end_string = ''
        if end:
            end_string = f' [{", ".join(end)}]'
        out = pre + Colors.BLUE + fix_badchars(name) + Colors.RESET
        out += f'{Colors.GRAY}{end_string}{Colors.RESET}'
        sys.stdout.write(f'{out}\n')

    @classmethod
    def print_archive_native(cls: Type[CLASSTYPE], pre: str,
                             name: str, archive: str) -> None:
        """archive to stdout"""
        out = pre + Colors.YELLOW + fix_badchars(name) + Colors.RESET
        out += f' {Colors.GRAY}[{cls.ARCHIVE}:{archive}]{Colors.RESET}'
        sys.stdout.write(f'{out}\n')
