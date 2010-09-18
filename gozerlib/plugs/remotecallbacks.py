# gozerlib/plugs/remotecallbacks.py
#
#

""" dispatch remote events. """

## gozerlib imports

from gozerlib.utils.lazydict import LazyDict
from gozerlib.utils.generic import strippedtxt, fromenc
from gozerlib.utils.exception import handle_exception
from gozerlib.callbacks import callbacks, remote_callbacks, first_callbacks
from gozerlib.container import Container
from gozerlib.eventbase import EventBase
from gozerlib.errors import NoProperDigest
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.contrib.xmlstream import NodeBuilder, XMLescape, XMLunescape

## basic imports

from simplejson import loads, dumps
import logging
import copy
import hmac
import hashlib

## defines

cpy = copy.deepcopy

## callback

def remotecb(bot, event):
    """ dispatch an event. """
    try:
        container = Container().load(event.txt)
    except TypeError:
        handle_exception()
        logging.warn("remotecallbacks - not a remote event - %s " % event.userhost)
        return
    logging.debug('doing REMOTE callback')
    try:
        digest = hmac.new(str(container.hashkey), container.payload, hashlib.sha512).hexdigest()
        logging.warn("forward - digest is %s" % digest)
    except TypeError:
        handle_exception()
        logging.error("forward - can't load payload - %s" % container.payload)
        return
    if container.digest == digest: e = EventBase().load(XMLunescape(container.payload))
    else: raise NoProperDigest()
    e.nodispatch = True
    e.forwarded = True
    bot.doevent(e)
    event.status = "done"  
    return

remote_callbacks.add("MESSAGE", remotecb)
	