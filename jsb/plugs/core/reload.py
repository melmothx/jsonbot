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
    for plug in pluglist:
        modname = bot.plugs.getmodule(plug)
        if not modname: errors.append("can't find %s plugin" % plug) ; continue
        try:
            loaded = bot.plugs.reload(modname, force=True, showerror=True)
            for plug in loaded:
                reloaded.append(plug)
                logging.warn("reload - %s reloaded" % plug) 
        except NoSuchPlugin: errors.append("can't find %s plugin" % plug) ; continue
        except Exception, ex:
            if 'No module named' in str(ex) and plug in str(ex):
                logging.debug('reload - %s - %s' % (modname, str(ex)))
                continue
            errors.append(exceptionmsg())
        update_mod(modname)
    if errors: ievent.reply('errors: ', errors)
    if reloaded: ievent.reply('reloaded: ', reloaded)

cmnds.add('reload', handle_reload, 'OPER')
examples.add('reload', 'reload <plugin>', 'reload core')
