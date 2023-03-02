"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

Catcli exceptions
"""


class CatcliException(Exception):
    """generic catcli exception"""


class BadFormatException(CatcliException):
    """use of bad format"""
