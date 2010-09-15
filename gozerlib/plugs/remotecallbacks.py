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
from gozerlib.remote.event import RemoteEvent
from gozerlib.errors import NoProperDigest
from gozerlib.gatekeeper import GateKeeper
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
gatekeeper = GateKeeper('gatekeeper-remote')

## callback

def preremotecb(bot, event):
    if gatekeeper.isblocked(event.auth or event.userhost): return False
    if event.txt.startswith("{"): return True
    return False

def remotecb(bot, event):
    """ dispatch an event. """
    try:
        container = Container().load(event.txt)
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

def handle_remoteallow(bot, event):
    if not event.rest:
        event.missing("<userhost>")
        return
    gatekeeper.allow(event.rest)
    event.done()
       
cmnds.add('remote-allow', handle_remoteallow, 'OPER')
examples.add('remote-allow', 'add JID of remote bot that we allow to receice events from', 'remote-allow jsonbot@appspot.com')

def handle_remotedeny(bot, event):
    if not event.rest:
        event.missing("<userhost>")
        return
    gatekeeper.deny(event.rest)
    event.done()
       
cmnds.add('remote-deny', handle_remotedeny, 'OPER')
examples.add('remote-deny', 'remove JID of remote bot', 'remote-deny evilfscker@pissof.com')
