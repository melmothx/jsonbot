# gozerlib/plugs/remotecallbacks.py
#
#

""" dispatch remote events. """

## gozerlib imports

from gozerlib.callbacks import callbacks, remote_callbacks
from gozerlib.container import Container
from gozerlib.remote.event import RemoteEvent
from gozerlib.errors import NoProperDigest

## basic imports

from simplejson import loads
import logging
import copy
import hmac
import hashlib

## defines

cpy = copy.deepcopy

## callback

if True:

    def preremotecb(bot, event):
        if event.txt.startswith("{"):
            return True
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
            e = RemoteEvent()
            try:
                digest = hmac.new(container.hashkey, container.payload, hashlib.sha512).hexdigest()
                logging.debug("forward - digest is %s" % digest)
                if container.digest == digest:
                    e.copyin(loads(container.payload))
                else:
                    raise NoProperDigest()

            except TypeError:
                logging.error("forward - can't load payload - %s" % container.payload)
                return

            remote_callbacks.check(bot, e)
            e.leave()
            return

    callbacks.add("MESSAGE", remotecb, preremotecb)
