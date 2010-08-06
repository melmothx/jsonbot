# gozerlib/plugs/welcome.py
#
#

from gozerlib.commands import cmnds

def handle_welcome(bot, event):
    event.reply("Welcome to JSONBOT .. The JSON everywhere bot ;] for wave/web/xmpp/IRC/console - you can give this bot commands. try !help.")

cmnds.add('welcome', handle_welcome, ['USER', 'OPER', 'GUEST'])
