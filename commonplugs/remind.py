# commonplugs/remind.py
#
#

""" remind people .. say txt when somebody gets active """

## gozerlib imports

from gozerlib.utils.generic import getwho
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.callbacks import callbacks
from gozerlib.datadir import datadir
from gozerlib.persist import PlugPersist

## basic imports

import time
import os

## classes

class Remind(PlugPersist):

    """ remind object """

    def __init__(self, name):
        PlugPersist.__init__(self, name)

    def add(self, who, data):
        """ add a remind txt """
        if not self.data.has_key(who):
             self.data[who] = []
        self.data[who].append(data)
        self.save()

    def wouldremind(self, userhost):
        """ check if there is a remind for userhost """
        try:
            reminds = self.data[userhost]
            if reminds == None or reminds == []:
                return False
        except KeyError:
            return False
        return True

    def remind(self, bot, userhost):
        """ send a user all registered reminds """
        reminds = self.data[userhost]
        if not reminds:
            return
        for i in reminds:
            ttime = None
            try:
                (tonick, fromnick, txt, ttime) = i
            except ValueError:
                (tonick, fromnick, txt) = i
            txtformat = '[%s] %s wants to remind you of: %s'
            if ttime:
                timestr = time.ctime(ttime)
            else:
                timestr = None
            bot.saynocb(tonick, txtformat % (timestr, fromnick, txt))
            bot.saynocb(fromnick, '[%s] reminded %s of: %s' % (timestr, tonick, txt))
        del self.data[userhost]
        self.save()

## defines

remind = Remind('remind.data')
assert remind

## callbacks

def preremind(bot, ievent):
    """ remind precondition """
    return remind.wouldremind(ievent.userhost)

def remindcb(bot, ievent):
    """ remind callbacks """
    remind.remind(bot, ievent.userhost)

# monitor privmsg and joins
callbacks.add('PRIVMSG', remindcb, preremind, threaded=True)
callbacks.add('JOIN', remindcb, preremind, threaded=True)
callbacks.add('MESSAGE', remindcb, preremind, threaded=True)
callbacks.add('WEB', remindcb, preremind, threaded=True)

## commands

def handle_remind(bot, ievent):
    """ remind <nick> <txt> .. add a remind """
    try:
        who = ievent.args[0]
        txt = ' '.join(ievent.args[1:])
    except IndexError:
        ievent.missing('<nick> <txt>')
        return
    if not txt:
        ievent.missing('<nick> <txt>')
        return
    userhost = getwho(bot, who)
    if not userhost:
        ievent.reply("can't find userhost for %s" % who)
        return
    else:
        remind.add(userhost, [who, ievent.nick, txt, time.time()])
        ievent.reply("remind for %s added" % who)

cmnds.add('remind', handle_remind, 'USER', allowqueue=False)
examples.add('remind', 'remind <nick> <txt>', 'remind dunker check the bot !')
