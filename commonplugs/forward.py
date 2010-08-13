# commonplugs/forward.py
#
#

""" forward incoming trafic on a bot to another bot through xmpp. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks, gn_callbacks, last_callbacks, first_callbacks
from gozerlib.eventbase import EventBase
from gozerlib.remote.event import Container, RemoteEvent
from gozerlib.persist import PlugPersist
from gozerlib.utils.lazydict import LazyDict
from gozerlib.examples import examples
from gozerlib.fleet import fleet
from gozerlib.config import cfg
from gozerlib.container import Container
from gozerlib.errors import NoProperDigest
from gozerlib.utils.exception import handle_exception
## basic imports

import logging
import copy
import time
import types
import hmac 
import hashlib

## simpljejson imports

from simplejson import loads, dumps

## defines

forward = PlugPersist("forward-core")
if not forward.data.allowin:
    forward.data.allowin = []
if not forward.data.channels:
    forward.data.channels = {}
if not forward.data.outs:
    forward.data.outs = {}
if not forward.data.whitelist:
    forward.data.whitelist = {}

cpy = copy.deepcopy

## callbacks

def forwardoutpre(bot, event):
    logging.debug("forward - pre - %s" % event.channel)
    if event.channel in forward.data.channels and not event.isremote:
        if not event.how == "background":
            return True

def forwardoutcb(bot, event):
    e = cpy(event)
    logging.debug("forward - cbtype is %s" % event.cbtype)
    e.isremote = True
    e.forwarded = True
    e.source = bot.jid
    outbot = fleet.getfirstjabber()
    if bot.isgae and not outbot:
        outbot = fleet.makebot('xmpp', 'forwardbot')
    if outbot:
        e.source = outbot.jid
        for jid in forward.data.channels[event.channel]:
            logging.info("forward - sending to %s" % jid)
            container = Container(outbot.jid, e.dump())
            container.isremote = True
            outbot.saynocb(jid, container.dump()) 
    else:
        logging.debug("forward - no xmpp bot found in fleet")

first_callbacks.add('BLIP_SUBMITTED', forwardoutcb, forwardoutpre)
first_callbacks.add('MESSAGE', forwardoutcb, forwardoutpre)
first_callbacks.add('PRESENCE', forwardoutcb, forwardoutpre)
first_callbacks.add('PRIVMSG', forwardoutcb, forwardoutpre)
first_callbacks.add('JOIN', forwardoutcb, forwardoutpre)
first_callbacks.add('PART', forwardoutcb, forwardoutpre)
first_callbacks.add('QUIT', forwardoutcb, forwardoutpre)
first_callbacks.add('NICK', forwardoutcb, forwardoutpre)
first_callbacks.add('CONSOLE', forwardoutcb, forwardoutpre)
first_callbacks.add('WEB', forwardoutcb, forwardoutpre)
first_callbacks.add('DISPATCH', forwardoutcb, forwardoutpre)
first_callbacks.add('OUTPUT', forwardoutcb, forwardoutpre)

def forwardinpre(bot, event):
    if event.forwarded:
        return True

def forwardincb(bot, event):
    if cfg.strictforward and not forward_allow(event.channel):
        return

    container = Container()
    container.load(event.txt)     
    container.isremote = True
    remoteevent = RemoteEvent()
    remoteevent.isremote = True
    remoteevent.printto = event.printto
    remoteevent.forwarded = True
    try:
        digest = hmac.new(container.hashkey, container.payload, hashlib.sha512).hexdigest()
        logging.debug("forward - digest is %s" % digest)
        if container.digest == digest:
            #logging.debug("forward - using payload - %s" % container.payload)
            remoteevent.copyin(loads(container.payload))
        else:
            raise NoProperDigest()

    except TypeError:
        handle_exception()
        logging.error("forward - can't load payload - %s" % container.payload)
        return
    #logging.debug(u"forward - incoming - %s" % remoteevent.dump())
    gn_callbacks.check(bot, remoteevent)

gn_callbacks.add('MESSAGE', forwardincb, forwardinpre)

## commands

def handle_forwardadd(bot, event):
    if not event.rest:
        event.missing('<JID>')
        return
    if "@" in event.rest:
        forward.data.outs[event.rest] = bot.type
        forward.save()
        event.done()

cmnds.add("forward-add", handle_forwardadd, 'OPER')
examples.add("forward-add" , "add an JID to forward to", "forward-add jsoncloud@appspot.com")

def handle_forwarddel(bot, event):
    if not event.rest:
        event.missing('<JID>')
        return
    del forward.data.outs[event.rest]
    forward.save()
    event.done()

cmnds.add("forward-del", handle_forwarddel, 'OPER')
examples.add("forward-del" , "delete an JID to forward to", "forward-del jsoncloud@appspot.com")

def handle_forwardallow(bot, event):
    if not event.rest:
        event.missing("<JID>")
        return
    if forward.data.whitelist.has_key(event.rest):
        forward.data.whitelist[event.rest] = bot.type
        forward.save()
    event.done()

cmnds.add("forward-allow", handle_forwardallow, 'OPER')
examples.add("forward-allow" , "allow an JID to forward to us", "forward-allow jsoncloud@appspot.com")

def handle_forwardlist(bot, event):
    try:
        event.reply("forwards for %s: " % event.channel, forward.data.channels[event.channel])
    except KeyError:
        event.reply("no forwards for %s" % event.channel)

cmnds.add("forward-list", handle_forwardlist, 'OPER')
examples.add("forward-list" , "list all forwards of a channel", "forward-list")

def handle_forward(bot, event):
    if not event.args:
        event.missing("<JID>")
        return

    forward.data.channels[event.channel] =  event.args
    for jid in event.args:
        forward.data.outs[jid] = bot.type
    forward.save()
    event.done()

cmnds.add("forward", handle_forward, 'OPER')
examples.add("forward" , "forward a channel to provided JIDS", "forward jsoncloud@appspot.com")

def handle_forwardstop(bot, event):
    if not event.args:
        event.missing("<JID>")
        return

    try:
        del forward.data.channels[event.channel]
        for jid in event.args:
            del forward.data.outs[jid]
        forward.save()
        event.done()
    except KeyError, ex:
         event.reply("we are not forwarding %s" %  str(ex))

cmnds.add("forward-stop", handle_forwardstop, 'OPER')
examples.add("forward-stop" , "stop forwarding a channel to provided JIDS", "forward-stop jsoncloud@appspot.com")
