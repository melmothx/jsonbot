# gozerlib/utils/name.py
#
#

""" name related helper functions. """

## basic imports

import string
import os

## defines

allowednamechars = string.ascii_letters + string.digits + '!.@-+#'

## stripname function
def stripname(name, allowed=""):
    """ strip all not allowed chars from name. """
    name = name.lower()
    res = ""
    for c in name:
        if ord(c) < 31: res += "-"
        elif c in allowednamechars + allowed: res += c
        else: res += "-"
    res = res.replace(os.sep, '+')
    res = res.replace("@", '+')
    res = res.replace("#", '+')
    res = res.encode("utf-8")
    return res

## testnam function

def testname(name):
    """ test if name is correct. """
    for c in name:
        if c not in allowedchars or ord(c) < 31: return False
    return True
