# gozerbot/utils/reboot.py
#
#

"""
     reboot code. 

"""

## gozerlib imports

from gozerlib.fleet import fleet
from gozerlib.config import cfg as config

## basic imports

from simplejson import dump
import os
import sys
import pickle
import tempfile

def reboot():

    """
        reboot the bot.

        .. literalinclude:: ../../gozerbot/reboot.py
            :pyobject: reboot

    """

    os.execl(sys.argv[0], *sys.argv)

def reboot_stateful(bot, ievent, fleet, partyline):
    """
        reboot the bot, but keep the connections.

        :param bot: bot on which the reboot command is given
        :type bot: gozerbot.botbase.BotBase	
        :param ievent: event that triggered the reboot
        :type ievent: gozerbot.eventbase. EventBase
        :param fleet: the fleet of the bot
        :type fleet: gozerbot.fleet.Fleet
        :param partyline: partyline of the bot
        :type partyline: gozerbot.partyline.PartyLine

        .. literalinclude:: ../../gozerbot/reboot.py
            :pyobject: reboot_stateful

    """
    config.reload()
    session = {'bots': {}, 'name': bot.name, 'channel': ievent.channel, 'partyline': []}

    for i in fleet.bots:
        session['bots'].update(i._resumedata())

    session['partyline'] = partyline._resumedata()
    sessionfile = tempfile.mkstemp('-session', 'gozerbot-')[1]
    dump(session, open(sessionfile, 'w'))
    fleet.save()
    fleet.exit(jabber=True)
    os.execl(sys.argv[0], sys.argv[0], '-r', sessionfile)

