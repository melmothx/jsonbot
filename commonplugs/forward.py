# commonplugs/forward.py
#
#

""" forward incoming trafic on a bot to another bot through xmpp. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks
from gozerlib.remote.event import Container
from gozerlib.persist import PlugPersist
from gozerlib.utils.lazydict import LazyDict
from gozerlib.examples import examples
from gozerlib.fleet import fleet

## basic imports

import logging
import copy

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

cpy = copy.deepcopy

## callbacks

def forwardoutpre(bot, event):
    if not event.isremote:
        return True

def forwardoutcb(bot, event):
    if not event.channel in forward.data.channels:
        return
    e = cpy(event)
    e.isremote = True
    container = Container(bot.jid, e.dump(), 'forward')
    outbot = fleet.getfirstjabber()
    if outbot:
        for jid in forward.data.outs:
            logging.warn("forward - sending to %s" % jid)
            outbot.out(jid, container.toxml(), event, bot.jid, False)
    else:
        logging.debug("forward - no xmpp bot found in fleet")

callbacks.add('ALL', forwardoutcb, forwardoutpre)

def forwardinpre(bot, event):
    if event.isremote:
        return True

def forwardincb(bot, event):
    if not forward_allow(event.channel):
        return
    
    container = LazyDict(loads(eventin))
    remoteevent = cpy(event)
    bot = fleet.makebot(container.type, "incoming-%s" % container.type)
    event = loads(container.payload)
    event.isremote = True
    event.ttl = 1
    bot.doevent(event)

callbacks.add('MESSAGE', forwardincb, forwardinpre)

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
    forward.data.whitelist[event.rest] = bot.type
    forward.save()
    event.done()

cmnds.add("forward-allow", handle_forwardallow, 'OPER')
examples.add("forward-allow" , "allow an JID to forward to us", "forward-allow jsoncloud@appspot.com")

def handle_forwardlist(bot, event):
    event.reply(forward.data.channels[event.channel])

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
