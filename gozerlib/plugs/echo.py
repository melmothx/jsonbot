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
    if not event.isdcc:
        if event.cbtype == "OUTPUT": bot.outnocb(event.channel, u"[!] %s" % event.txt, event=event, dotime=True)
        else: bot.outnocb(event.channel, u"[%s] %s" % (event.nick, event.txt), event=event, dotime=True)

callbacks.add("DISPATCH", echocb, echopre, threaded=True)
first_callbacks.add("OUTPUT", echocb, echopre, threaded=True)

## echo command

def handle_echo(bot, event):
    """ echo txt to user. """
    if event.how != "background" and not event.iscmnd() and not event.isremote:
        if not event.isdcc: bot.saynocb(event.channel, u"[%s] %s" % (event.nick, event.txt))
            
cmnds.add("echo", handle_echo, ['USER', 'GUEST'])
examples.add("echo", "echo input", "echo yoooo dudes")
