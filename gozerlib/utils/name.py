# gozerlib/utils/name.py
#
#

""" name related helper functions. """

## basic imports

import string

## define

allowednamechars = string.ascii_letters + string.digits + '!.@'

## functions

def stripname(name):
    """ strip all not allowed chars from name. """
    res = ""
    for c in name:
        if c in allowednamechars:
            res += c

    return res

def testname(name):
    """ test if name is correct. """
    for c in name:
        if c not in allowedchars:
            return False

    return True
