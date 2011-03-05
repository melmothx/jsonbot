# jsb.plugs.common/echo.py
#
#

""" echo typed sentences. """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.callbacks import callbacks, first_callbacks

## basic imports

import logging

## echo callback

def echopre(bot, event):
    if event.how != "background" and bot.type == "web" and not event.forwarded and not event.cbtype == "OUTPUT": return True
    return False

def echocb(bot, event):
    bot.outnocb(event.channel, u"[%s] %s" % (event.nick, event.txt), event=event, dotime=False)

first_callbacks.add("DISPATCH", echocb, echopre)

## echo command

def handle_echo(bot, event):
    """ echo txt to user. """
    if event.how != "background" and not event.iscmnd() and not event.isremote:
        if not event.isdcc: bot.saynocb(event.channel, u"[%s] %s" % (event.nick, event.txt))
            
cmnds.add("echo", handle_echo, ['OPER'])
examples.add("echo", "echo input", "echo yoooo dudes")
