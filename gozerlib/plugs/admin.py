# gozerlib/plugs/admin.py
#
#

""" admin related commands. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persist import Persist
from gozerlib.boot import savecmndtable, savepluginlist, boot
from gozerlib.admin import plugin_packages
from gozerlib.config import cfg
from gozerlib.plugins import plugs
from gozerlib.botbase import BotBase

## simplejson imports

from simplejson import dump

## commands

def handle_adminboot(bot, ievent):
    """ boot the bot .. do some initialisation. """
    boot(force=True)
    ievent.done()

cmnds.add('admin-boot', handle_adminboot, 'OPER')
cmnds.add('admin-init', handle_adminboot, 'OPER')
examples.add('admin-boot', 'initialize the bot .. cmndtable and pluginlist', 'admin-init')

def handle_loadall(bot, ievent):
    """ load all available plugins. """
    plugs.loadall(plugin_packages)
    ievent.done()

cmnds.add('admin-loadall', handle_loadall, 'OPER')
examples.add('admin-loadall', 'load all plugins', 'admin-loadall')

def handle_adminmakebot(bot, ievent):
    """ <name> <type> .. create a bot of given type. """
    try:
        botname, bottype = ievent.args
    except ValueError:
        ievent.missing("<name> <type>")
        return

    newbot = BotBase()
    newbot.botname = botname
    newbot.type = bottype
    newbot.owner = bot.owner
    newbot.save()
    ievent.done()

cmnds.add('admin-makebot', handle_adminmakebot, 'OPER')
examples.add('admin-makebot', 'create a bot', 'admin-makebot cmndxmpp xmpp')
