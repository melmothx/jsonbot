# gozerlib/utils/id.py
#
#

""" id related functions. """

## gozerlib imports

from gozerlib.utils.generic import toenc

## basic imports

import uuid

## getrssid function

def getrssid(url, time):
    """ get an id based on url and time. """
    key = unicode(url) + unicode(time)
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, toenc(key)))
