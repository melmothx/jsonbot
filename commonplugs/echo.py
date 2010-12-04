# commonplugs/echo.py
#
#

""" echo typed sentences. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.callbacks import callbacks, first_callbacks

## basic imports

import logging

## echo callback

def echopre(bot, event):
    logging.warn("%s - echo pre %s" % (bot.name, event.cbtype))
    if event.how != "background": return True
    return False

def echocb(bot, event):
    if not event.isdcc: bot.outnocb(event.channel, u"[%s] %s" % (event.nick, event.txt), dotime=True)

callbacks.add("DISPATCH", echocb, echopre, nr=100)
first_callbacks.add("OUTPUT", echocb, echopre, nr=100)

## echo command

def handle_echo(bot, event):
    """ echo txt to user. """
    if event.how != "background" and not event.iscmnd() and not event.isremote:
        if not event.isdcc: bot.saynocb(event.channel, u"[%s] %s" % (event.nick, event.txt))
            
cmnds.add("echo", handle_echo, ['USER', 'GUEST'])
examples.add("echo", "echo input", "echo yoooo dudes")
