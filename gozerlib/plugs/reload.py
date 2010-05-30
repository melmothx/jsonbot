# gozerbot/plugs/reload.py
#
#

""" reload plugin. """

## gozerlib imports

from gozerlib.utils.exception import handle_exception, exceptionmsg
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.boot import plugin_packages, savecmndtable, savepluginlist

## basic imports

import os

def handle_reload(bot, ievent):
    """ <list of plugins> .. reload plugins. """
    try:
        pluglist = ievent.args
    except IndexError:
        ievent.missing('<list plugins>')
        return

    reloaded = []
    errors = []

    for plug in pluglist:
        for package in plugin_packages:
            modname = "%s.%s" % (package, plug)
            try:
                if bot.plugs.reload(modname, force=True):
                    reloaded.append(modname)
                    break
            except Exception, ex:
                if 'No module named' in str(ex):
                    continue
                errors.append(exceptionmsg())

    if reloaded:
        ievent.reply('reloaded: ', reloaded)
    if errors:
        ievent.reply('errors: ', errors)

cmnds.add('reload', handle_reload, 'OPER')
examples.add('reload', 'reload <plugin>', 'reload core')

def handle_unload(bot, ievent):
    """ unload a plugin. """
    try:
        what = ievent.args[0].lower()
    except IndexError:
        ievent.missing('<plugin>')
        return

    if not what in bot.plugs:
        ievent.reply('there is no %s module' % what)
        return

    got = bot.plugs.unload(what)
    ievent.reply("unloaded and disabled: ", got)

cmnds.add('unload', handle_unload, 'OPER')
examples.add('unload', 'unload <plugin>', 'unload relay')
