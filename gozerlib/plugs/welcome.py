# gozerlib/plugs/welcome.py
#
#

from gozerlib.commands import cmnds

def handle_welcome(bot, event):
    event.reply("Welcome to JSONBOT .. The JSON everywhere bot ;] for wave/web/xmpp/IRC/console")

cmnds.add('welcome', handle_welcome, ['USER', 'GUEST'])
