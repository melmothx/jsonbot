# gozerlib/container.py
#
#

""" container for bot to bot communication. """

## gozerlib imports

from gozerlib.gozerevent import GozerEvent

## basic imports

import hmac
import uuid
import time

## defines

idattributes = ['origin', 'type', 'payload', 'idtime']

## functions

def getid(container):
    name = ""
    for attr in idattributes:
        try:
            name += str(container[attr])
        except KeyError:
            pass
    return uuid.uuid3(uuid.NAMESPACE_URL, name).hex

## classes

class Container(GozerEvent):

    def __init__(self, origin=None, payload=None, type="event"):
        GozerEvent.__init__(self)
        self.createtime = time.time()
        self.origin = origin
        self.payload = payload
        self.type = str(type) 
        self.makeid()

    def makeid(self):
        self.idtime = time.time()
        self.id = getid(self)
