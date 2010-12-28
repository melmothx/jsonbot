# jsb/plugs/admin.py
#
#

""" admin related commands. """

## jsb imports

from jsb.lib.eventhandler import mainhandler
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persist import Persist
from jsb.lib.boot import savecmndtable, savepluginlist, boot, plugin_packages, clear_tables, getcmndtable, getcallbacktable
from jsb.lib.plugins import plugs
from jsb.lib.botbase import BotBase
from jsb.lib.exit import globalshutdown

## admin-boot command

def handle_adminboot(bot, ievent):
    """ boot the bot .. do some initialisation. """
    if 'saveperms' in ievent.rest:
        boot(force=True, saveperms=True)
    else:
        boot(force=True, saveperms=False)
    ievent.done()

cmnds.add('admin-boot', handle_adminboot, 'OPER')
cmnds.add('admin-init', handle_adminboot, 'OPER')
examples.add('admin-boot', 'initialize the bot .. cmndtable and pluginlist', 'admin-boot')

## admin-loadall command

def handle_admintables(bot, ievent):
    """ load all available plugins. """
    if ievent.rest == "cmnd": ievent.reply(unicode(getcmndtable()))
    else: ievent.reply(unicode(getcallbacktable()))
    ievent.done()

cmnds.add('admin-tables', handle_admintables, 'OPER')
examples.add('admin-tables', 'show runtime tables', 'admin-tables')

## admin-loadall command

def handle_loadall(bot, ievent):
    """ load all available plugins. """
    plugs.loadall(plugin_packages)
    ievent.done()

cmnds.add('admin-loadall', handle_loadall, 'OPER', threaded=True)
examples.add('admin-loadall', 'load all plugins', 'admin-loadall')

## admin-makebot command

def handle_adminmakebot(bot, ievent):
    """ create a bot of given type. """
    try: botname, bottype = ievent.args
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

## admin-stop command

def handle_adminstop(bot, ievent):
    if bot.isgae:
        ievent.reply("this command doesn't work on the GAE")
        return
    mainhandler.put(0, globalshutdown)

cmnds.add("admin-stop", handle_adminstop, "OPER")
examples.add("admin-stop", "stop the bot.", "stop")