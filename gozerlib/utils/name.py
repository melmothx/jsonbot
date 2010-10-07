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
    res = u""
    name = name.encode("utf-8")
    for c in name:
        if ord(c) < 31: continue
        else: res += c
    res =  res.replace(os.sep, '+')
    return res

## testnam function

def testname(name):
    """ test if name is correct. """
    for c in name:
        if c not in allowedchars or ord(c) < 31: return False
    return True
