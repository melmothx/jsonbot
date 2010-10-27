# gozerlib/utils/name.py
#
#

""" name related helper functions. """

## basic imports

import string
import os
import re

## defines

allowednamechars = string.ascii_letters + string.digits + '!.@-+#'

## slugify function taken from django

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    return re.sub('[-\s]+', '-', value)



## stripname function
def stripname(name, allowed=""):
    """ strip all not allowed chars from name. """
    res = u""
    for c in name:
        if ord(c) < 31: continue
        else: res += c
    res = res.replace(os.sep, '=')
#    res = res.replace("@", '+')
#    res = res.replace("#", '-')
#    res = res.replace("~", '_')
#    res = res.replace("$", '^')
#    res = res.replace("`", "'")
#    res = res.replace(">", ".")
#    res = res.replace("<", ",")
#    res = res.replace("|", "!")
    return slugify(res)

## testnam function

def testname(name):
    """ test if name is correct. """
    for c in name:
        if c not in allowedchars or ord(c) < 31: return False
    return True
