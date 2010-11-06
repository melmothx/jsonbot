# plugs/idle.py
#
#

""" show how long someone has been idle. """

## gozerlib imports

from gozerlib.utils.timeutils import elapsedstring
from gozerlib.utils.generic import getwho
from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks
from gozerlib.examples import examples
from gozerlib.persist import PlugPersist

## basic imports

import time
import os
import logging

## defines

idle = PlugPersist('idle.data')
if not idle.data:
    idle.data = {}

## callbacks

def preidle(bot, event):
    """ idle precondition aka check if it is not a command """
    if bot.isgae and event.userhost not in bot.cfg.followlist:
        return False
    else:
        return True
        
def idlecb(bot, event):
    """ idle PRIVMSG callback .. set time for channel and nick """
    ttime = time.time()
    idle.data[event.userhost] = ttime
    idle.data[event.channel] = ttime
    idle.save()

callbacks.add('PRIVMSG', idlecb, preidle)
callbacks.add('MESSAGE', idlecb, preidle)
callbacks.add('WEB', idlecb, preidle)
callbacks.add('CONSOLE', idlecb, preidle)
callbacks.add('DISPATCH', idlecb, preidle)

## commands

def handle_idle(bot, ievent):
    """ idle [<nick>] .. show how idle an channel/user has been """
    try:
        who = ievent.args[0]
    except IndexError:
        handle_idle2(bot, ievent)
        return
    userhost = getwho(bot, who)
    if not userhost:
        ievent.reply("can't get userhost of %s" % who)
        return
    logging.warn("idle - userhost is %s" % userhost)
    try:
        elapsed = elapsedstring(time.time() - idle.data[userhost])
    except KeyError:
        ievent.reply("i haven't seen %s" % who)
        return
    if elapsed:
        ievent.reply("%s is idle for %s" % (who, elapsed))
        return
    else:
        ievent.reply("%s is not idle" % who)
        return   

cmnds.add('idle', handle_idle, ['USER', 'GUEST'])

def handle_idle2(bot, ievent):
    """ show how idle a channel has been """
    chan = ievent.channel
    try:
        elapsed = elapsedstring(time.time()-idle.data[chan])
    except KeyError:
        ievent.reply("nobody said anything on channel %s yet" % chan)
        return
    if elapsed:
        ievent.reply("channel %s is idle for %s" % (chan, elapsed))
    else:
        ievent.reply("channel %s is not idle" % chan)

examples.add('idle', 'idle [<nick>] .. show how idle the channel is or show \
how idle <nick> is', '1) idle 2) idle test')
