# jsb.plugs.common/learn.py
#
#

""" learn information items .. facts .. factoids. """

## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.utils.lazydict import LazyDict
from jsb.lib.persist import PlugPersist

## basic imports

import logging

## commands

def handle_learn(bot, event):
    """" set an information item. """
    if not event.rest: event.missing("<item> is <description>") ; return
    try: (what, description) = event.rest.split(" is ", 1)
    except ValueError: event.missing("<item> is <description>") ; return
    what = what.lower()
    items = PlugPersist(event.channel)
    if not items.data: items.data = LazyDict()
    if not items.data.has_key(what): items.data[what] = []
    if description not in items.data[what]: items.data[what].append(description)
    items.save()
    event.reply("%s item added to %s database" % (what, event.channel))

cmnds.add('learn', handle_learn, ['USER', 'GUEST'])
examples.add('learn', 'learn the bot a description of an item.', "learn dunk is botpapa")

def handle_forget(bot, event):
    """" set an information item. """
    if not event.rest: event.missing("<item> and <match>") ; return
    try: (what, match) = event.rest.split(" and ", 2)
    except ValueError: event.missing("<item> and <match>") ; return
    what = what.lower()
    items = PlugPersist(event.channel)
    if not items.data: items.data = LazyDict()
    if items.data.has_key(what):
        for i in range(len(items.data[what])):
            if match in items.data[what][i]:
                del items.data[what][i]                
                items.save()
                break
    event.reply("item removed from %s database" % event.channel)

cmnds.add('forget', handle_forget, ['USER'])
examples.add('forget', 'forget a description of an item.', "forget dunk and botpapa")

def handle_whatis(bot, event):
    items = PlugPersist(event.channel)
    what = event.rest.lower().split('!')[0].strip()
    if what in items.data and items.data[what]: event.reply("%s is " % event.rest, items.data[what], dot=", ")
    else: event.reply("no information known about %s" % what)

cmnds.add('whatis', handle_whatis, ['USER', 'GUEST'])
examples.add("whatis", "whatis learned about a subject", "whatis jsb")

def prelearn(bot, event):
    if event.txt and event.txt[0] == "?" and not event.forwarded: return True
    return False

def learncb(bot, event):
    event.bind(bot)
    items = PlugPersist(event.channel)
    target = event.txt[1:].lower().split('!')[0].strip()
    if target in items.data: event.reply("%s is " % target, items.data[target], dot=", ")

callbacks.add("PRIVMSG", learncb, prelearn)
callbacks.add("MESSAGE", learncb, prelearn)
callbacks.add("DISPATCH", learncb, prelearn)
callbacks.add("CONSOLE", learncb, prelearn)
callbacks.add("CMND", learncb, prelearn)
