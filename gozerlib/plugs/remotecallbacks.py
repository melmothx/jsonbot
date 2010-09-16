# gozerlib/plugs/remotecallbacks.py
#
#

""" dispatch remote events. """

## gozerlib imports

from gozerlib.utils.generic import strippedtxt, fromenc
from gozerlib.utils.exception import handle_exception
from gozerlib.callbacks import callbacks, remote_callbacks, first_callbacks
from gozerlib.container import Container
from gozerlib.eventbase import EventBase
from gozerlib.errors import NoProperDigest
from gozerlib.commands import cmnds
from gozerlib.examples import examples

## basic imports

from simplejson import loads
import logging
import copy
import hmac
import hashlib

## defines

cpy = copy.deepcopy

## callback

def preremotecb(bot, event):
    if event.txt.startswith("{"): return True
    return False

def remotecb(bot, event):
    """ dispatch an event. """
    try:
        #container = Container().load(event.txt)
        container = Container(event.txt)
    except TypeError:
        logging.debug("remotecallbacks - not a remote event - %s " % event.userhost)
        return
    if container.isremote:
        logging.debug('doing REMOTE callback')
        e = EventBase()
        #e.parse(event)
        try:
            digest = hmac.new(str(container.hashkey), str(container.payload), hashlib.sha512).hexdigest()
            logging.debug("forward - digest is %s" % digest)
        except TypeError:
            handle_exception()
            logging.error("forward - can't load payload - %s" % container.payload)
            return
        if container.digest == digest:
            e.load(container.payload)
        else:
            raise NoProperDigest()
        e.prepare(bot)
        remote_callbacks.check(bot, e)
        event.status = "done"  
        return

first_callbacks.add("MESSAGE", remotecb, preremotecb)
