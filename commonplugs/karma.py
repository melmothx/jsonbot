# commonplugs/karma.py
#
#

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persist import PlugPersist
from gozerlib.utils.statdict import StatDict

## basic imports

import logging

## KarmaItem class

class KarmaItem(PlugPersist):

     def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.count = self.data.count or 0
         self.data.whoup = self.data.whoup or {}
         self.data.whodown = self.data.whodown or {}
         self.data.whyup = self.data.whyup or []
         self.data.whydown = self.data.whydown or []

## karma precondition

def prekarma(bot, event):
    if event.iscmnd(): return True
    return False

## karma callbacks

def karmacb(bot, event):
    try: target = event.txt[1:].lower()
    except IndexError: return
    item = item2 = rest = reason = None
    try: item, rest = target.split("++", 1)
    except ValueError:
        try: item2, rest = target.split("--", 1)
        except ValueError: return
    try: reason = rest.split('#', 1)[1]
    except IndexError: reason = None
    if item:
        i = KarmaItem(event.channel + "-" + item)
        i.data.count += 1
        if event.nick not in i.data.whoup: i.data.whoup[event.nick] = 0
        i.data.whoup[event.nick] += 1
        if reason and reason not in i.data.whyup: i.data.whyup.append(reason)
        i.save()
    else:
        i = KarmaItem(event.channel + "-" + item2)
        i.data.count -= 1
        if event.nick not in i.data.whodown: i.data.whodown[event.nick] = 0
        i.data.whodown[event.nick] -= 1
        if reason and reason not in i.data.whyup: i.data.whydown.append(reason)
        i.save()
    got = item or item2
    event.bind(bot)
    event.reply("karma of %s is now %s" % (got, i.data.count))

callbacks.add('PRIVMSG', karmacb, prekarma)
callbacks.add('MESSAGE', karmacb, prekarma)

## karma command

def handle_karma(bot, event):
    if not event.rest: event.missing("<what>") ; return
    k = event.rest.lower()
    item = KarmaItem(event.channel + "-" + k)
    if item.data.count: event.reply("karma of %s is %s" % (k, item.data.count))
    else: event.reply("%s doesn't have karma yet." % k)

cmnds.add('karma', handle_karma, ['USER', ])
examples.add('karma', 'show karma', 'karma jsonbot')

def handle_karmawhyup(bot, event):
    k = event.rest.lower()
    item = KarmaItem(event.channel + "-" + k)
    if item.data.whyup: event.reply("reasons for karma up are: ", item.data.whyup)
    else: event.reply("no reasons for karmaup of %s known yet" % k)

cmnds.add("karma-whyup", handle_karmawhyup, ['USER', ])
examples.add("karma-whyup", "show why a karma item is upped", "karma-whyup jsonbot")

def handle_karmawhoup(bot, event):
    k = event.rest.lower()
    item = KarmaItem(event.channel + "-" + k)
    sd = StatDict(item.data.whoup)
    res = []
    for i in sd.top():
        res.append("%s: %s" % i)
    if item.data.whoup: event.reply("uppers of karma up are: ", res)
    else: event.reply("nobody upped %s yet" % k)

cmnds.add("karma-whoup", handle_karmawhoup, ['USER', ])
examples.add("karma-whoup", "show who upped an item", "karma-whoup jsonbot")

def handle_karmawhydown(bot, event):
    k = event.rest.lower()
    item = KarmaItem(event.channel + "-" + k)
    if item.data.whydown: event.reply("reasons for karma up are: ", item.data.whydown)
    else: event.reply("no reasons for karmaup of %s known yet" % k)

cmnds.add("karma-whydown", handle_karmawhydown, ['USER', ])
examples.add("karma-whydown", "show why a karma item is downed", "karma-whydown jsonbot")

def handle_karmawhodown(bot, event):
    k = event.rest.lower()
    item = KarmaItem(event.channel + "-" + k)
    sd = StatDict(item.data.whodown)
    res = []
    for i in sd.down():
        res.append("%s: %s" % i)
    if item.data.whodown: event.reply("downers of karma up are: ", res)
    else: event.reply("nobody downed %s yet" % k)

cmnds.add("karma-whodown", handle_karmawhodown, ['USER', ])
examples.add("karma-whodown", "show who downed an item", "karma-whodown jsonbot")
