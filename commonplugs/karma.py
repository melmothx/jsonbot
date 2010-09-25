# commonplugs/karma.py
#
#

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persist import PlugPersist

## basic imports

import logging

## karma precondition

def prekarma(bot, event):
    if event.iscmnd(): return True
    return False

## karma callbacks

def karmacb(bot, event):
    try: target = event.txt[1:].lower()
    except IndexError: return
    item = item2 = rest = None
    try: item, rest = target.split("++", 1)
    except ValueError:
        try: item2, rest = target.split("--", 1)
        except ValueError: return
    karma = PlugPersist(event.channel + ".core")
    if item:
        try: karma.data[item] += 1
        except KeyError: karma.data[item] = 1
    else:
        try: karma.data[item2] -= 1
        except KeyError: karma.data[item2] = -1
    got = item or item2
    karma.save()
    event.reply("karma of %s is now %s" % (got, karma.data[got]))
    if rest: 
        reason = rest.split('#', 1)
        if reason[0]:
            if item: r = PlugPersist(self.channel + ".reasonup")
            else: r = PlugPersist(self.channel + ".reasondown")
            r.data[item or item2] = reason[0]
            r.save()

callbacks.add('PRIVMSG', karmacb, prekarma)
callbacks.add('MESSAGE', karmacb, prekarma)

## karma command

def handle_karma(bot, event):
    if not event.rest: event.missing("<what>") ; return
    karma = PlugPersist(event.channel + ".core")
    k = event.rest.lower()
    try: event.reply("karma of %s is %s" % (k, karma.data[k]))
    except KeyError: event.reply("%s doesn't have karma yet." % k)

cmnds.add('karma', handle_karma, ['USER', ])
examples.add('karma', 'show karma', 'karma jsonbot')

def handle_karmawhyup(bot, event):
    k = event.rest
    reasons = PlugPersist(event.channel + ".reasonup")
    try: event.reply("reasons for karma up are: ", reasons.data[k])
    except KeyError: event.reply("no reasons for karmaup of %s known yet" % k)

cmnds.add("karma-whyup", handle_karmawhyup, ['USER', ])
examples.add("karma-whyup", "show why a karma item is upped", "karma-whyup jsonbot")
