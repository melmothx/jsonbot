# gozerlib/plugs/core.py
#
#

""" core bot commands. """

## gozerbot imports

from gozerlib.utils.statdict import StatDict
from gozerlib.utils.log import setloglevel
from gozerlib.utils.timeutils import elapsedstring
from gozerlib.utils.generic import getversion
from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.plugins import plugs
from gozerlib.boot import plugin_packages, getpluginlist, boot
from gozerlib.persist import Persist
from gozerlib.reboot import reboot, reboot_stateful
from gozerlib.eventhandler import mainhandler
from gozerlib.fleet import fleet
from gozerlib.socklib.partyline import partyline

## basic imports

import time
import threading
import sys
import re
import os
import copy
import cgi

## define

cpy = copy.deepcopy

## commands

def handle_reboot(bot, ievent):
    if bot.isgae:
        ievent.reply("this command doesn't work on the GAE")
        return
    ievent.reply("rebooting")
    time.sleep(5)
    if ievent.rest == "cold":
        stateful = False
    else:
        stateful = True

    if stateful:
        #if fleet.size():
        #    fleet.exit()
        #else:
        #    bot.exit()
        mainhandler.put(0, reboot_stateful, bot, ievent, fleet, partyline)
    else:
        bot.exit()
        mainhandler.put(0, reboot)

cmnds.add("reboot", handle_reboot, "OPER")
examples.add("reboot", "reboot the bot.", "reboot")

def handle_quit(bot, ievent):
    if bot.isgae:
        ievent.reply("this command doesnt work on the GAE")
        return
    ievent.reply("quiting")
    bot.exit()

cmnds.add("quit", handle_quit, "OPER")
examples.add("quit", "quit the bot.", "quit")

def handle_encoding(bot, ievent):
    """ show default encoding. """
    ievent.reply('default encoding is %s' % sys.getdefaultencoding())

cmnds.add('encoding', handle_encoding, ['USER', 'OPER'])
examples.add('encoding', 'show default encoding', 'encoding')

def handle_uptime(bot, ievent):
    """ show uptime. """
    ievent.reply("uptime is %s" % elapsedstring(time.time()-bot.starttime))

cmnds.add('uptime', handle_uptime, ['USER', 'WEB', 'GUEST'])
examples.add('uptime', 'show uptime of the bot', 'uptime')

def handle_list(bot, ievent):
    """ [<plugin>] .. list loaded plugins or list commands provided by plugin. """
    try:
        what = ievent.args[0]
    except:
        # no arguments given .. show plugins
        result = []
        for plug in plugs:
            if '__init__' in plug:
                continue

            result.append(plug.split('.')[-1])

        ievent.reply('loaded plugins: ', result)
        return

    # show commands of <what> plugin
    result = []
    for i, j in cmnds.iteritems():
        if what == j.plugname:
            txt = i
            if txt:
                result.append(txt)

    if result:
        result.sort()
        ievent.reply('%s has the following commands: ' % what, result)
    else:
        ievent.reply('no commands found for plugin %s' % what)

#cmnds.add('list', handle_list, ['USER', 'WEB', 'CLOUD'], threaded=True)

def handle_available(bot, ievent):
    """ show available plugins .. to enable use !reload. """
    ievent.reply("available plugins: ", getpluginlist(), raw=True)

cmnds.add('list', handle_available, ['USER', 'GUEST'])
examples.add('list', 'list available plugins', 'list')

def handle_commands(bot, ievent):
    """ <plugin> .. show commands of <plugin>. """
    try:
        plugin = ievent.args[0].lower()
    except IndexError:
        plugin = ""

    result = []
    cp = dict(cmnds)
    for i, j in cp.iteritems():
        if not plugin or plugin == j.plugname:
            txt = i
            if txt:
                result.append(txt)

    if result:
        result.sort()
        ievent.reply('%s has the following commands: ' % plugin, result)
    else:
        ievent.reply('no commands found for plugin %s' % plugin)

cmnds.add('commands', handle_commands, ['USER', 'GUEST', 'CLOUD'])
examples.add('commands', 'show commands of <plugin>', '1) commands core')

def handle_perm(bot, ievent):

    """ <command> .. get permission of command. """

    try:
        cmnd = ievent.args[0]
    except IndexError:
        ievent.missing("<cmnd>")
        return

    try:
        perms = cmnds.perms(cmnd)
    except KeyError:
        ievent.reply("no %sw command registered")
        return

    if perms:
        ievent.reply("%s command needs %s permission" % (cmnd, perms))
        return

    ievent.reply("can't find perm for %s" % cmnd)

cmnds.add('perm', handle_perm, ['USER', 'GUEST', 'WEB'])
examples.add('perm', 'show permission of command', 'perm quit')

def handle_version(bot, ievent):
    """ show bot's version. """
    ievent.reply(getversion(bot.type.upper()))

cmnds.add('version', handle_version, ['USER', 'GUEST'])
examples.add('version', 'show version of the bot', 'version')

def handle_whereis(bot, ievent):
    """ <cmnd> .. locate a command. """
    try:
        cmnd = ievent.args[0]
    except IndexError:
        ievent.missing('<cmnd>')
        return

    plugin = cmnds.whereis(cmnd)
    if plugin:
        ievent.reply("%s command is in: %s" %  (cmnd, plugin))
    else:
        ievent.reply("can't find " + cmnd)

cmnds.add('whereis', handle_whereis, ['USER', 'GUEST'])
examples.add('whereis', 'whereis <cmnd> .. show in which plugins <what> is', 'whereis test')

#def handle_help(bot, event):
#    """ help [<cmnd>|<plugin>]. """
#    if event.rest:
#        event.txt = 'help ' + event.rest
#        handle_helpplug(bot, event)
#        return
#    event.reply("see !help <plugin> for help on a plugin and !list for a list of available plugins.")

#cmnds.add('help', handle_help, ['USER', 'GUEST'])

def handle_helpplug(bot, ievent):

    """ help [<plugin>] .. show help on plugin/command or show basic help msg. """

    try:
        what = ievent.args[0]
    except IndexError:
        ievent.reply("available plugins: ", getpluginlist(), raw=True)
        ievent.reply('see !help <plugin> for help on a plugin.')
        return

    plugin = None
    modname = ""

    for package in plugin_packages:
        try:
             modname = "%s.%s" % (package, what)
             plugin = plugs.reload(modname)
             if plugin:
                 break
        except(KeyError, ImportError):
             pass

    if not plugin:
        ievent.reply("no %s plugin loaded" % what)
        return

    try:
          phelp = plugin.__doc__
    except (KeyError, AttributeError):
        ievent.reply('no description of %s plugin available' % what)
        return

    cmndresult = []
      
    if phelp:

        if bot.users:
            perms = bot.users.getperms(ievent.userhost)

        if not perms:
            perms = ['GUEST', ]

        for i, j in cmnds.iteritems():
            if what == j.plugname:
                for perm in j.perms:
                    if perm in perms:
                        if True:
                            try:
                                descr = j.func.__doc__.strip()
                                cmndhelp = cmnds.gethelp(i)
                                try:
                                    cmndresult.append(u"    !%s - %s - examples: %s" % (i, descr, examples[i].example))
                                except KeyError:
                                    cmndresult.append(u"    !%s - %s - no examples" % (i, descr))

                            except AttributeError:
                                cmndresult.append(i)

    if cmndresult and phelp:
        res = []
        for r in cmndresult:
            if bot.type in ['web', ]:
                res.append("<i>%s</i>" % cgi.escape(r))
            else:
                res.append(r)

        res.sort()
        what = what.upper()
        if bot.type in ['web', ]:
            txt = '<b>HELP ON %s</b><br><br><b><i>%s</i></b><br><br>%s' % (what, phelp.strip(), "<br>".join(res))
            ievent.reply(txt)
        else:
            res.insert(0, u'%s - %s\n' % (what, phelp.strip()))
            ievent.reply('HELP ON %s\n\n' % what, res, dot="\n", raw=True)
    else:
        ievent.reply('no commands available')


cmnds.add('help', handle_helpplug, ['USER', 'GUEST'])
examples.add('help', 'get help on <cmnd> or <plugin>', '1) help-plug test 2) help-plug misc')

def handle_apro(bot, ievent):
    """ <cmnd> .. apropos for command. """
    try:
        what = ievent.args[0]
    except IndexError:
        ievent.missing('<what>')
        return

    result = []
    perms = bot.users.getperms(ievent.userhost)

    for i in cmnds.apropos(re.escape(what)):
        result.append(i)

    if result:
        ievent.reply("commands matching %s: " % what, result)
    else: 
        ievent.reply('no matching commands found for %s (%s)' % (what, ' .. '.join(perms)))

cmnds.add('apro', handle_apro, ['USER', 'GUEST'])
examples.add('apro', 'apro <what> .. search for commands that contain <what>', 'apro com')

def handle_whatcommands(bot, ievent):
    """ show all commands with permission. """
    if not ievent.rest:
        ievent.missing('<perm>')
        return

    result = cmnds
    res = []
    for cmnd in result.values():
        if ievent.rest in cmnd.perms:
            res.append(cmnd.cmnd)

    res.sort()
    if not res:
        ievent.reply('no commands known for permission %s' % ievent.rest)
    else:
        ievent.reply('commands known for permission %s: ' % ievent.rest, res)

cmnds.add('whatcommands', handle_whatcommands, ['USER', 'GUEST'])
examples.add('whatcommands', 'show commands with permission <perm>', 'whatcommands USER')

def handle_versions(bot, ievent):
    """ show versions of all loaded modules (if available). """
    versions = {}
    for mod in copy.copy(sys.modules):
        try:
            versions[mod] = sys.modules[mod].__version__
        except AttributeError, ex:
            pass
        try:
            versions['python'] = sys.version
        except AttributeError, ex:
            pass

    ievent.reply("versions ==> %s" % str(versions))
    

cmnds.add('versions', handle_versions, 'OPER')
examples.add('versions', 'show versions of all loaded modules', 'versions')

def handle_loglevel(bot, event):
    if not event.rest:
        event.missing("<loglevel> (string)")
        return
    setloglevel(event.rest)
    event.done()

cmnds.add("loglevel", handle_loglevel, "OPER")
examples.add("logleve;", "set loglevel ot on of debug, info, warning or error", "loglevel debug")

def handle_botdata(bot, event):
    result = bot.dump()
    event.reply(str(result))

cmnds.add("bot-data", handle_botdata, 'OPER')
examples.add("bot-data", "show data of the bot", "bot-data")

def handle_threads(bot, ievent):

    """ show running threads. """

    try:
         import threading
    except ImportError:
         ievent.reply("threading is not enabled.")
         return

    stats = StatDict()
    threadlist = threading.enumerate()

    for thread in threadlist:
        stats.upitem(thread.getName())

    result = []

    for item in stats.top():
        result.append("%s = %s" % (item[0], item[1]))

    result.sort()
    ievent.reply("threads running: ", result)

cmnds.add('threads', handle_threads, ['USER', 'OPER'])
examples.add('threads', 'show running threads', 'threads')

def handle_statusline(bot, event):
    if event.chan.data.feeds:
        event.reply("<b>controlchars:</b> %s - <b>perms:</b> %s - <b>modfied:</b> %s - <b>feeds:</b> %s - <b>cache:</b> %s" % (event.chan.data.cc, ", ".join(event.user.data.perms), time.ctime(event.chan.lastmodified), ", ".join(event.chan.data.feeds), len(event.chan.data.outcache)), raw=True)
    elif event.chan.data.cc:
        event.reply("<b>controlchars:</b> %s - <b>perms:</b> %s - <b>modfied:</b> %s - <b>feeds:</b> no feeds - <b>cache:</b> %s" % (event.chan.data.cc, ", ".join(event.user.data.perms), time.ctime(event.chan.lastmodified), len(event.chan.data.outcache)), raw=True)
    else:
        event.reply("<b>controlchars:</b> ! - <b>perms:</b> %s - <b>modfied:</b> %s - <b>feeds:</b> no feeds - <b>cache:</b> %s" % (", ".join(event.user.data.perms), time.ctime(event.chan.lastmodified), len(event.chan.data.outcache)), raw=True)

cmnds.add('statusline', handle_statusline, ['OPER', 'USER', 'GUEST'])
examples.add('statusline', 'show status line', 'statusline')
