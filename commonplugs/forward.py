# commonplugs/forward.py
#
#

""" forward incoming trafic on a bot to another bot through xmpp. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks, remote_callbacks, last_callbacks, first_callbacks
from gozerlib.eventbase import EventBase
from gozerlib.persist import PlugPersist
from gozerlib.utils.lazydict import LazyDict
from gozerlib.examples import examples
from gozerlib.fleet import fleet
from gozerlib.config import cfg
from gozerlib.container import Container
from gozerlib.errors import NoProperDigest
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.locking import locked

## commonplugs imports

from commonplugs.twitter import postmsg

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

## forward precondition

def forwardoutpre(bot, event):
    """ preconditon to check if forward callbacks is to be fired. """
    chan = unicode(event.channel).lower()
    if not chan: return
    logging.debug("forward - pre - %s" % event.channel)
    if chan in forward.data.channels and not event.isremote() and not event.forwarded:
        if event.how != u"background": return True
    return False

## forward callbacks

def forwardoutcb(bot, event): 
    """ forward callback. """
    e = cpy(event)
    logging.debug("forward - cbtype is %s - %s" % (event.cbtype, event.how))
    e.forwarded = True
    e.source = bot.jid
    e.botname = bot.server or bot.name
    for jid in forward.data.channels[event.channel.lower()]:
        logging.warn("forward - sending to %s" % jid)
        if jid == "twitter":
            try: postmsg(forward.data.outs[jid], e.txt)
            except Exception, ex: handle_exception()
            continue
        outbot = fleet.getfirstjabber(bot.isgae)
        if not outbot and bot.isgae: outbot = fleet.makebot('xmpp', 'forwardbot')
        if outbot:
            e.source = outbot.jid
            txt = outbot.normalize(e.tojson())
            container = Container(outbot.jid, txt)
            outbot.outnocb(jid, container.tojson()) 
        else: logging.error("forward - no xmpp bot found in fleet".upper())

first_callbacks.add('BLIP_SUBMITTED', forwardoutcb, forwardoutpre)
first_callbacks.add('MESSAGE', forwardoutcb, forwardoutpre)
#first_callbacks.add('PRESENCE', forwardoutcb, forwardoutpre)
first_callbacks.add('PRIVMSG', forwardoutcb, forwardoutpre)
first_callbacks.add('JOIN', forwardoutcb, forwardoutpre)
first_callbacks.add('PART', forwardoutcb, forwardoutpre)
first_callbacks.add('QUIT', forwardoutcb, forwardoutpre)
first_callbacks.add('NICK', forwardoutcb, forwardoutpre)
first_callbacks.add('CONSOLE', forwardoutcb, forwardoutpre)
first_callbacks.add('WEB', forwardoutcb, forwardoutpre)
first_callbacks.add('DISPATCH', forwardoutcb, forwardoutpre)
first_callbacks.add('OUTPUT', forwardoutcb, forwardoutpre)

## forward-add command

def handle_forwardadd(bot, event):
    """ add a new forward. """
    if not event.rest:
        event.missing('<JID>')
        return
    if "@" in event.rest:
        forward.data.outs[event.rest] = event.user.data.name
        forward.save()
        if not event.rest in event.chan.forwards: event.chan.forwards.append(event.rest)
    if event.rest:
        event.chan.save()
        event.done()

cmnds.add("forward-add", handle_forwardadd, 'OPER')
examples.add("forward-add" , "add an JID to forward to", "forward-add jsoncloud@appspot.com")

## forward-del command

def handle_forwarddel(bot, event):
    """ delete a forward. """
    if not event.rest:
        event.missing('<JID>')
        return
    del forward.data.outs[event.rest]
    forward.save()
    event.done()

cmnds.add("forward-del", handle_forwarddel, 'OPER')
examples.add("forward-del" , "delete an JID to forward to", "forward-del jsoncloud@appspot.com")

## forward-allow command

def handle_forwardallow(bot, event):
    """ allow a remote bot to forward to us. """
    if not event.rest:
        event.missing("<JID>")
        return
    if forward.data.whitelist.has_key(event.rest):
        forward.data.whitelist[event.rest] = bot.type
        forward.save()
    event.done()

cmnds.add("forward-allow", handle_forwardallow, 'OPER')
examples.add("forward-allow" , "allow an JID to forward to us", "forward-allow jsoncloud@appspot.com")

## forward-list command

def handle_forwardlist(bot, event):
    """ list forwards. """
    try: event.reply("forwards for %s: " % event.channel, forward.data.channels[event.channel])
    except KeyError: event.reply("no forwards for %s" % event.channel)

cmnds.add("forward-list", handle_forwardlist, 'OPER')
examples.add("forward-list" , "list all forwards of a channel", "forward-list")

## forward command

def handle_forward(bot, event):
    """ forward the channel tot another bot. """
    if not event.args:
        event.missing("<JID>")
        return
    forward.data.channels[event.channel.lower()] =  event.args
    for jid in event.args:
        forward.data.outs[jid] = event.user.data.name
        if not jid in event.chan.data.forwards: event.chan.data.forwards = event.args
    if event.args: event.chan.save()
    forward.save()
    event.done()

cmnds.add("forward", handle_forward, 'OPER')
examples.add("forward" , "forward a channel to provided JIDS", "forward jsoncloud@appspot.com")

## forward-stop command

def handle_forwardstop(bot, event):
    """ stop forwarding the channel to another bot. """
    if not event.args:
        event.missing("<JID>")
        return

    try:
        for jid in event.args:
            try:
                forward.data.channels[event.channel].remove(jid)
                del forward.data.outs[jid]
                if jid in event.chan.data.forwards: event.chan.data.forwards.remove(jid)
            except ValueError: pass
        forward.save()
        event.done()
    except KeyError, ex: event.reply("we are not forwarding %s" %  str(ex))

cmnds.add("forward-stop", handle_forwardstop, 'OPER')
examples.add("forward-stop" , "stop forwarding a channel to provided JIDS", "forward-stop jsoncloud@appspot.com")
