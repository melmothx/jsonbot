# commonplugs/echo.py
#
#

""" echo typed in sentences. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.callbacks import callbacks

## basic imports

import logging

## commands

def handle_echo(bot, event):
    """ echo txt to user. """
    if event.how != "background" and not event.iscmnd():
        if not event.isdcc:
            bot.saynocb(event.userhost, u"[%s] %s" % (event.nick, event.txt))
            
cmnds.add("echo", handle_echo, ['USER', 'OPER', 'GUEST'], threaded=True)
examples.add("echo", "echo input", "echo yoooo dudes")

callbacks.add("DISPATCH", handle_echo, threaded=True)
callbacks.add("OUTPUT", handle_echo, threaded=True)
