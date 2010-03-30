# gozerlib/plugs/welcome.py
#
#

from gozerlib.commands import cmnds

def handle_welcome(bot, event):
    event.reply("Welcome to JSONBOT.")

cmnds.add('welcome', handle_welcome, ['USER', 'GUEST'])
