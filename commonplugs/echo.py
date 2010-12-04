# commonplugs/echo.py
#
#

""" echo typed sentences. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.callbacks import callbacks

## basic imports

import logging

## echo callback

def echopre(bot, event):
    if event.cbtype == "OUTPUT" and bot.type == "WEB": return True
    return bot.type == "web" and not event.how == "background"

def echocb(bot, event):
    bot.outnocb(event.channel, event.txt, event=event, dotime=True)

callbacks.add("OUTPUT", echocb, echopre)
callbacks.add("DISPATCH", echocb, echopre)

## echo command

def handle_echo(bot, event):
    """ echo txt to user. """
    if event.how != "background" and not event.iscmnd() and not event.isremote:
        if not event.isdcc: bot.saynocb(event.userhost, u"[%s] %s" % (event.nick, event.txt))
            
cmnds.add("echo", handle_echo, ['USER', 'GUEST'], threaded=True)
examples.add("echo", "echo input", "echo yoooo dudes")
