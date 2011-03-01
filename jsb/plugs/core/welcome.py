# jsb/plugs/welcome.py
#
#

""" send welcome message. """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples

## welcome command

def handle_welcome(bot, event):
    event.reply("Welcome to JSONBOT - you can give this bot commands. try !help.")

cmnds.add('welcome', handle_welcome, ['USER', 'GUEST'])
examples.add('welcome', 'send welcome msg', 'welcome')
