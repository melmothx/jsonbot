# gozerbot/plugs/reload.py
#
#

""" reload plugin. """

## jsb imports

from jsb.utils.exception import handle_exception, exceptionmsg
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.boot import savecmndtable, savepluginlist, update_mod
from jsb.lib.errors import NoSuchPlugin

## basic imports

import os
import logging

## reload command

def handle_reload(bot, ievent):
    """ reload list of plugins. """
    try: pluglist = ievent.args
    except IndexError:
        ievent.missing('<list plugins>')
        return
    reloaded = []
    errors = []
    from jsb.lib.boot import plugin_packages
    for plug in pluglist:
        for package in plugin_packages:
            modname = "%s.%s" % (package, plug)
            try:
                if bot.plugs.reload(modname, force=True, showerror=False):
                    update_mod(modname)
                    reloaded.append(modname)
                    logging.warn("reload - %s reloaded" % modname) 
                    break
            except NoSuchPlugin: continue
            except Exception, ex:
                if 'No module named' in str(ex):
                    logging.debug('reload - %s - %s' % (modname, str(ex)))
                    continue
                errors.append(exceptionmsg())
    if reloaded: ievent.reply('reloaded: ', reloaded)
    if errors: ievent.reply('errors: ', errors)

cmnds.add('reload', handle_reload, 'OPER')
examples.add('reload', 'reload <plugin>', 'reload core')
