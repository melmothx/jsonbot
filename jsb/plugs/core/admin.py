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
from jsb.utils.generic import stringsed

## admin-boot command

def handle_adminboot(bot, ievent):
    """ boot the bot .. do some initialisation. """
    if 'saveperms' in ievent.rest: boot(force=True, saveperms=True)
    else: boot(force=True, saveperms=False)
    ievent.done()

cmnds.add('admin-boot', handle_adminboot, 'OPER')
examples.add('admin-boot', 'initialize the bot .. cmndtable and pluginlist', 'admin-boot')

## admin-commands

def handle_admincommands(bot, ievent):
    """ load all available plugins. """
    cmnds = getcmndtable()
    if not ievent.rest: ievent.reply("commands: ", cmnds)
    else:
        try: ievent.reply("%s command is found in %s " % (ievent.rest, cmnds[ievent.rest]))
        except KeyError: ievent.reply("no such commands available") 

cmnds.add('admin-commands', handle_admincommands, 'OPER')
examples.add('admin-commands', 'show runtime command table', 'admin-commands')

## admin-callbacks

def handle_admincallbacks(bot, ievent):
    """ load all available plugins. """
    cbs = getcallbacktable()
    if not ievent.rest: ievent.reply("callbacks: ", cbs)
    else:
        try: ievent.reply("%s callbacks: " % ievent.rest, cbs[ievent.rest])
        except KeyError: ievent.reply("no such callbacks available") 

cmnds.add('admin-callbacks', handle_admincallbacks, 'OPER')
examples.add('admin-callbacks', 'show runtime callback table', 'admin-callbacks')

## admin-loadall command

def handle_loadall(bot, ievent):
    """ load all available plugins. """
    plugs.loadall(plugin_packages, force=True)
    ievent.done()

cmnds.add('admin-loadall', handle_loadall, 'OPER', threaded=True)
examples.add('admin-loadall', 'load all plugins', 'admin-loadall')

## admin-makebot command

def handle_adminmakebot(bot, ievent):
    """ create a bot of given type. """
    try: botname, bottype = ievent.args
    except ValueError: ievent.missing("<name> <type>") ; return
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
    if bot.isgae: ievent.reply("this command doesn't work on the GAE") ; return
    mainhandler.put(0, globalshutdown)

cmnds.add("admin-stop", handle_adminstop, "OPER")
examples.add("admin-stop", "stop the bot.", "stop")

def handle_adminupgrade(bot, event):
    if not bot.isgae: event.reply("this command only works in GAE") ; return
    else: import google
    from jsb.lib.persist import JSONindb
    teller = 0
    props = JSONindb.properties()
    for d in JSONindb.all():
        try:
            dd = d.filename
            if not "gozerdata" in dd: continue
            if 'run' in dd: continue
            ddd = stringsed(dd, "s/%s/%s/" % ("gozerdata", "data"))
            ddd = stringsed(ddd, "s/waveplugs/jsb.plugs.wave/")
            ddd = stringsed(ddd, "s/gozerlib\.plugs/jsb.plugs.core/")
            ddd = stringsed(ddd, "s/commonplugs/jsb.plugs.common/")  
            ddd = stringsed(ddd, "s/socketplugs/jsb.plugs.socket/")  
            ddd = stringsed(ddd, "s/gaeplugs/jsb.plugs.gae/")
            if d.get_by_key_name(ddd): continue 
            d.filename = ddd
            kwds = {}
            for prop in props: kwds[prop] = getattr(d, prop)
            d.get_or_insert(ddd, **kwds)
            bot.say(event.channel, "UPGRADED %s" % ddd)
            teller += 1
        except Exception, ex: bot.say(event.channel, str(ex))
    bot.say(event.channel, "DONE - upgraded %s items" % teller)

cmnds.add("admin-upgrade", handle_adminupgrade, "OPER", threaded=True)
examples.add("admin-upgrade", "upgrade the GAE bot", "admin-upgrade")

def handle_adminsetstatus(bot, event):
    if bot.type != "sxmpp": event.reply("this command only works on sxmpp bots (for now)") ; return
    if not event.rest: event.missing("<status> [<show>]") ; return
    status = event.args[0]
    try: show = event.args[1]
    except IndexError: show = ""
    bot.setstatus(status, show)

cmnds.add("admin-setstatus", handle_adminsetstatus, ["GUEST", "USER", "OPER"])
examples.add("admin-setstatus", "set status of sxmpp bot", "admin-setstatus available Yooo dudes !")
