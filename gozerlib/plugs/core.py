# commonplugs/core.py
#
#

""" core bot commands. """

## gozerbot imports

from gozerlib.utils.timeutils import elapsedstring
from gozerlib.utils.generic import getversion
from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.plugins import plugs
from gozerlib.admin import plugin_packages
from gozerlib.boot import getpluginlist, boot
from gozerlib.persist import Persist

## basic imports

import time
import threading
import sys
import re
import os
import copy

## define

def handle_ccadd(bot, event):
    """ add a control character (bot wide). """
    if bot.cfg:
        if not bot.cfg.cc:
            bot.cfg.cc = event.rest
        elif event.rest not in bof.cfg.cc:
            bot.cfg.cc += event.rest
        else:
            event.reply("%s is already in cc list" % event.rest)
            return
        bot.cfg.save()
        event.done()
    else:
        event.reply("bot.cfg is not set.")

cmnds.add('cc-add', handle_ccadd, 'OPER')
examples.add('cc-add', 'add a control charater (bot wide)', 'cc-add @')

def handle_ccremove(bot, event):
    """ remove a control character from the bot's cc list. """
    try:
        bot.cfg.cc.remove(event.rest)
        bot.cfg.save()
        event.done()
    except ValueError:
        event.reply("can't remove %s from %s" % (event.rest, bot.cfg.cc))

cmnds.add('cc-add', handle_ccadd, 'OPER')
examples.add('cc-add', 'add a control charater (bot wide)', 'cc-add @')

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
    ievent.reply("available plugins: ", getpluginlist())

cmnds.add('list', handle_available, ['USER', 'GUEST'])
examples.add('list', 'list available plugins', 'list')

def handle_commands(bot, ievent):
    """ <plugin> .. show commands of <plugin>. """
    try:
        plugin = ievent.args[0].lower()
    except IndexError:
        ievent.missing('<plugin> .. see the list command for available plugins')
        return

    if not plugs.has_key(plugin):
        ievent.reply('no %s plugin is loaded .. see the available command for available plugins (reload to enable)' % plugin)
        return

    result = []
    cp = dict(cmnds)
    for i, j in cp.iteritems():
        if plugin == j.plugname:
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

def handle_help(bot, event):
    """ help [<cmnd>|<plugin>]. """
    if event.rest:
        event.txt = 'help ' + event.rest
        handle_helpplug(bot, event)
        return
    event.reply("see !help <plugin> for help on a plugin and !list for a list of available plugins.")

cmnds.add('help', handle_help, ['USER', 'GUEST'])

def handle_helpplug(bot, ievent):

    """ help [<plugin>] .. show help on plugin/command or show basic help msg. """

    try:
        what = ievent.args[0]
    except IndexError:
        pluginslist = Persist('run' + os.sep + 'pluginlist').data
        ievent.reply("available plugins: ", pluginslist)
        ievent.reply('see commmands <plugin> for list of commands.')
        return

    cmndhelp = cmnds.gethelp(what)

    if cmndhelp:
        try:
            ievent.reply("examples: " + examples[what].example)
        except KeyError:
            pass

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
        ievent.reply('%s - %s' % (what, phelp))

        if bot.users:
            perms = list(bot.users.getperms(ievent.userhost))
        else:
            perms = ['GUEST', ]

        for i, j in cmnds.iteritems():
            if what == j.plugname:
                for perm in j.perms:
                    if perm in perms:
                        if i not in cmndresult:
                            try:
                                descr = j.func.__doc__
                                cmndresult.append("    !%s - %s" % (i,descr))
                            except AttributeError:
                                cmndresult.append(i)

    if cmndresult:
        cmndresult.sort()
        ievent.reply('commands: \n', cmndresult, dot="\n", raw=True)
    else:
        ievent.reply('no commands available')

cmnds.add('help-plug', handle_helpplug, ['USER', 'GUEST'])
examples.add('help-plug', 'get help on <cmnd> or <plugin>', '1) help-plug test 2) help-plug misc')

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
        ievent.reply("commands matching %s: " % what, result , nr=1)
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
