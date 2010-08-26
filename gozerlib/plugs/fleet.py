# gozerlib/plugs/fleet.py
#
#

""" 
    The fleet makes it possible to run multiple bots in one running instance.
    It is a list of bots.
"""

## gozerlib imports

from gozerlib.config import Config
from gozerlib.threads import start_new_thread
from gozerlib.fleet import fleet, FleetBotAlreadyExists
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.datadir import datadir
from gozerlib.utils.name import stripname

## basic imports

import os

## commands

def handle_fleetavail(bot, ievent):

    """ show available fleet bots. """

    ievent.reply('available bots: ', fleet.avail()) 

cmnds.add('fleet-avail', handle_fleetavail, 'OPER')
examples.add('fleet-avail', 'show available fleet bots', 'fleet-avail')

def handle_fleetconnect(bot, ievent):

    """ fleet-connect <botname> .. connect a fleet bot to it's server. """

    try:
        botname = ievent.args[0]
    except IndexError:
        ievent.missing('<botname>')
        return

    try:
        fleetbot = fleet.byname(botname)
        if fleetbot:
            start_new_thread(fleetbot.connect, ())
            ievent.reply('%s connect thread started' % botname)
        else:
            ievent.reply("can't connect %s .. trying enable" % botname)
            fleet.enable(bot, ievent)
    except Exception, ex:
        ievent.reply(str(ex))

cmnds.add('fleet-connect', handle_fleetconnect, 'OPER', threaded=True)
examples.add('fleet-connect', 'connect bot with <name> to irc server', 'fleet-connect test')

def handle_fleetdisconnect(bot, ievent):

    """ fleet-disconnect <botname> .. disconnect a fleet bot from server. """

    try:
        botname = ievent.args[0]
    except IndexError:
        ievent.missing('<botname>')
        return

    ievent.reply('exiting %s' % botname)

    try:
        if fleet.exit(botname):
            ievent.reply("%s bot stopped" % botname)
        else:
            ievent.reply("can't stop %s bot" % botname)
    except Exception, ex:
        ievent.reply(str(ex))

cmnds.add('fleet-disconnect', handle_fleetdisconnect, 'OPER', threaded=True)
examples.add('fleet-disconnect', 'fleet-disconnect <name> .. disconnect bot with <name> from irc server', 'fleet-disconnect test')

def handle_fleetlist(bot, ievent):

    """ fleet-list .. list bot names in fleet. """

    ievent.reply("fleet: ", fleet.list())

cmnds.add('fleet-list', handle_fleetlist, ['USER', 'WEB'])
examples.add('fleet-list', 'show current fleet list', 'fleet-list')

def handle_fleetdel(bot, ievent):

    """ fleet-del <botname> .. delete bot from fleet. """

    try:
        name = ievent.args[0]
    except IndexError:
        ievent.missing('<name>')
        return

    try:
        if fleet.delete(name):
            ievent.reply('%s deleted' % name)
        else:
            ievent.reply('%s delete failed' % name)
    except Exception, ex:
        ievent.reply(str(ex))

cmnds.add('fleet-del', handle_fleetdel, 'OPER', threaded=True)
examples.add('fleet-del', 'fleet-del <botname> .. delete bot from fleet list', 'fleet-del test')

def docmnd(bot, ievent):

    """ do command on bot/all bots. """

    try:
        name = ievent.args[0]
        cmnd = ' '.join(ievent.args[1:])
    except IndexError:
        ievent.missing('<name> <cmnd>')
        return

    if not cmnd:
        ievent.missing('<name> <cmnd>')
        return

    if cmnd.find('cmnd') != -1:
        ievent.reply("no looping please ;]")
        return

    try:
        if name == 'all':
            fleet.cmndall(ievent, cmnd)
        else:
            fleet.cmnd(ievent, name, cmnd)
    except Exception, ex:
        ievent.reply(str(ex))

cmnds.add('cmnd', docmnd, ['USER', 'WEB'], threaded=True)
examples.add('cmnd', "cmnd all|<botname> <cmnd> .. excecute command on bot with <name> or on all fleet bots", '1) cmnd main st 2) cmnd all st')

def fleet_disable(bot, ievent):

    """ disable a fleet bot. """

    if not ievent.rest:
        ievent.missing("list of fleet bots")
        return

    bots = ievent.rest.split()

    for name in bots:
        bot = fleet.byname(name)
        if bot:
            bot.cfg['enable'] = 0
            bot.cfg.save()
            ievent.reply('disabled %s' % name)
            fleet.exit(name)
        else:
            ievent.reply("can't find %s bot in fleet" % name)

cmnds.add('fleet-disable', fleet_disable, 'OPER')
examples.add('fleet-disable', 'disable a fleet bot', 'fleet-disable local')

def fleet_enable(bot, ievent):

    """ enable a fleet bot. """

    if not ievent.rest:
        ievent.missing("list of fleet bots")
        return

    bots = ievent.rest.split()

    for name in bots:
        bot = fleet.byname(name)

        if bot:
            bot.cfg.load()
            bot.cfg['disable'] = 0
            bot.cfg.save()
            ievent.reply('enabled %s' % name)
            start_new_thread(bot.connect, ())
        elif name in fleet.avail():
            cfg = Config('fleet' + os.sep + stripname(name) + os.sep + 'config')
            cfg['disable'] = 0
            cfg.save()
            bot = fleet.makebot(cfg.type, cfg.name, cfg)
            ievent.reply('enabled and started %s bot' % name)
            start_new_thread(bot.connect, ())
        else:
            ievent.reply('no %s bot in fleet' % name)

cmnds.add('fleet-enable', fleet_enable, 'OPER', threaded=True)
examples.add('fleet-enable', 'enable a fleet bot', 'fleet-enable local')
