# commonplugs/echo.py
#
#

""" echo typed in sentences. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.callbacks import callbacks


def handle_echo(bot, event):
    bot.say(event.userhost, u"[%s] %s" % (event.nick, event.txt))

cmnds.add("echo", handle_echo, ['USER', 'OPER', 'GUEST'])
examples.add("echo", "echo input", "echo yoooo dudes")

callbacks.add("WEB", handle_echo)
