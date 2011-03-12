# jsb/plugs/plug.py
#
#

""" plugin management. """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.boot import default_plugins, plugin_packages, remove_plugin, update_mod

## plug-enable command

def handle_plugenable(bot, event):
    if not event.rest: event.missing("<plugin>") ; return
    mod = bot.plugs.getmodule(event.rest)
    if not mod: event.reply("can't find module for %s" % event.rest) ; return
    event.reply("reloading and enabling %s" % mod)
    bot.enable(mod)
    bot.plugs.reload(mod, force=True)
    #update_mod(mod)
    event.done()

cmnds.add("plug-enable", handle_plugenable, ["OPER", ])
examples.add("plug-enable", "enable a plugin", "plug-enable jsb.plugs.common.rss")

## plug-disable command

def handle_plugdisable(bot, event):
    if not event.rest: event.missing("<plugin>") ; return
    mod = bot.plugs.getmodule(event.rest)
    if mod in default_plugins: event.reply("can't remove a default plugin") ; return
    if not mod: event.reply("can't find module for %s" % event.rest) ; return
    event.reply("unloading and disabling %s" % mod)
    bot.plugs.unload(mod)
    bot.disable(mod)
    #remove_plugin(mod)
    event.done()

cmnds.add("plug-disable", handle_plugdisable, ["OPER", ])
examples.add("plug-disable", "disable a plugin", "plug-disable jsb.plugs.common.rss")
