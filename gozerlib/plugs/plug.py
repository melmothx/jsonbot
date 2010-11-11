# gozerlib/plugs/plug.py
#
#

""" plugin management. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.boot import default_plugins, plugin_packages, update_mod

## plug-enable command

def handle_plugenable(bot, event):
    if not event.rest: event.missing("<plugin>") ; return
    mod = bot.plugs.whichmodule(event.rest)
    if not mod: event.reply("can't find module for %s" % event.rest) ; return
    event.reply("reloading and enabling %s" % mod)
    bot.plugs.enable(mod)
    bot.plugs.load(mod)
    update_mod(mod)
    event.done()

cmnds.add("plug-enable", handle_plugenable, ["OPER", ])
examples.add("plug-enable", "enable a plugin", "plug-enable commonplugs.rss")

## plug-disable command

def handle_plugdisable(bot, event):
    if not event.rest: event.missing("<plugin>") ; return
    if event.rest in default_plugins: event.reply("can't remove a default plugin") ; return
    mod = bot.plugs.whichmodule(event.rest)
    if not mod: event.reply("can't find module for %s" % event.rest) ; return
    event.reply("unloading and disabling %s" % mod)
    bot.plugs.unload(mod)
    bot.plugs.disable(mod)
    update_mod(mod)
    event.done()

cmnds.add("plug-disable", handle_plugdisable, ["OPER", ])
examples.add("plug-disable", "disable a plugin", "plug-disable commonplugs.rss")
