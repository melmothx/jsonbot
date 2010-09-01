# commonplugs/learn.py
#
#

""" learn information items .. facts .. factoids. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.lazydict import LazyDict

## commands

def handle_learn(bot, event):
    """" set an information item. """
    if not event.rest:
        event.missing("<item> is <description>")
        return
    try:
        (what, i, description) = event.rest.split(" ", 2)
    except ValueError:
        event.missing("<item> is <description>")
        return
        
    if not event.chan.data.info:
        event.chan.data.info = LazyDict()
    if not event.chan.data.info.has_key(what):
        event.chan.data.info[what] = []
    if description not in event.chan.data.info[what]:
        event.chan.data.info[what].append(description)
    event.chan.save()
    event.reply("item added to %s" % event.channel)

cmnds.add('learn', handle_learn, ['USER', 'OPER'])
cmnds.add('=', handle_learn, ['USER', 'OPER'])
examples.add('learn', 'learn the bot a description of an item.', "learn dunk is botpapa")

def handle_whatis(bot, event):
    if event.chan.data.info and event.chan.data.info.has_key(event.rest):
        event.reply("%s is " % event.rest, event.chan.data.info[event.rest], dot=" - ")
    else:
        event.reply("no information known about %s" % event.rest)

cmnds.add('whatis', handle_whatis, ['USER', 'OPER'])
cmnds.add('?', handle_whatis, ['USER', 'OPER'])
examples.add("whatis", "whatis learned about a subject", "whatis jsonbot")
