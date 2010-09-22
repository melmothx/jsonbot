# gozerlib/plugs/welcome.py
#
#

""" send welcome message. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples

## welcome command

def handle_welcome(bot, event):
    event.reply("Welcome to JSONBOT .. The JSON everywhere bot ;] for wave/web/xmpp/IRC/console - you can give this bot commands. try !help.")

cmnds.add('welcome', handle_welcome, ['USER', 'OPER', 'GUEST'])
exmaples.add('welcome', 'send welcome msg', 'welcome')
