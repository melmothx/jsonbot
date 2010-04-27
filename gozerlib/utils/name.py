# gozerlib/utils/name.py
#
#

""" name related helper functions. """

## basic imports

import string
import os

## define

allowednamechars = string.ascii_letters + string.digits + '!.@-'

## functions

def stripname(name, allowed=""):
    """ strip all not allowed chars from name. """
    res = ""
    for c in name:
        if ord(c) < 31:
            res += "-"
        elif c in allowednamechars + allowed:
            res += c
        else:
            res += "-"

    res.replace(os.sep, '-')
    return res

def testname(name):
    """ test if name is correct. """
    for c in name:
        if c not in allowedchars or ord(c) < 31:
            return False

    return True
