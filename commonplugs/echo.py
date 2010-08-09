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

def handle_echo(bot, event):
    logging.warn("echo - cbtype %s" % event.cbtype) 
    if event.how != "background" and not event.iscmnd():
        bot.say(event.userhost, u"[%s] %s" % (event.nick, event.txt))
    
cmnds.add("echo", handle_echo, ['USER', 'OPER', 'GUEST'])
examples.add("echo", "echo input", "echo yoooo dudes")

callbacks.add("GADGET", handle_echo)
callbacks.add("OUTPUT", handle_echo)
