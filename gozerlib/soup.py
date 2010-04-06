# gozerlib/soup.py
#
#

""" helper functions and classes for the JSONBOT event netwerk (jsonsoup). """

## gozerlib imports

from gozerlib.utils.lazydict import LazyDict

## defines

idattributes = ['origin', 'type', 'payload']

## functions

def getsoupid(container):
    name = ""
    for attr in idattributes:
        try:
            name += unicode(container[attr])
        except KeyError:
            pass
    return uuid.uuid3(uuid.NAMESPACE_URL, name).hex

## classes

class Container(LazyDict):

    def __init__(self, origin, payload, type="event"):
        self.origin = origing
        self.payload = payload
        self.type = type

    def makeid(self):
        self.id = getsoupid(self)
