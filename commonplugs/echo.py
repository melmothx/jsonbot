# commonplugs/echo.py
#
#

""" echo typed sentences. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples

## basic imports

import logging

## echo command

def handle_echo(bot, event):
    """ echo txt to user. """
    if event.how != "background" and not event.iscmnd() and not event.isremote:
        if not event.isdcc: bot.saynocb(event.userhost, u"[%s] %s" % (event.nick, event.txt))
            
cmnds.add("echo", handle_echo, ['USER', 'GUEST'], threaded=True)
examples.add("echo", "echo input", "echo yoooo dudes")
