# commonplugs/learn.py
#
#

""" learn information items .. facts .. factoids. """

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.lazydict import LazyDict
from gozerlib.persist import PlugPersist

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
cmnds.add('=', handle_learn, ['USER', 'GUEST'])
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
    what = event.rest.lower()
    if what in items.data and items.data[what]: event.reply("%s is " % event.rest, items.data[what], dot=", ")
    else: event.reply("no information known about %s" % what)

cmnds.add('whatis', handle_whatis, ['USER', 'GUEST'])
cmnds.add('?', handle_whatis, ['USER', 'OPER'])
examples.add("whatis", "whatis learned about a subject", "whatis jsonbot")

def prelearn(bot, event):
    if event.iscmnd() and not event.forwarded: return True
    return False

def learncb(bot, event):
    event.bind(bot)
    items = PlugPersist(event.channel)
    target = event.usercmnd[1:].lower()
    if target in items.data: event.reply("%s is " % target, items.data[target], dot=", ")

callbacks.add("PRIVMSG", learncb, prelearn)
callbacks.add("MESSAGE", learncb, prelearn)
callbacks.add("DISPATCH", learncb, prelearn)
