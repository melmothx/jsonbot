# gozerlib/reboot.py
#
#

""" reboot code. """

## gozerlib imports

from gozerlib.fleet import getfleet

## basic imports

from simplejson import dump
import os
import sys
import pickle
import tempfile
import logging

## reboot function

def reboot():
    """ reboot the bot. """
    logging.warn("reboot - rebooting")
    os.execl(sys.argv[0], *sys.argv)

## reboot_stateful function

def reboot_stateful(bot, ievent, fleet, partyline):
    """ reboot the bot, but keep the connections (IRC only). """
    logging.warn("reboot - doing statefull reboot")
    session = {'bots': {}, 'name': bot.name, 'channel': ievent.channel, 'partyline': []}
    for i in getfleet().bots:
        logging.warn("reboot - updating %s" % i.name)
        data = i._resumedata()
        if not data: continue
        session['bots'].update(data)
        if i.bottype == "sxmpp": i.exit()
    session['partyline'] = partyline._resumedata()
    sessionfile = tempfile.mkstemp('-session', 'jsonbot-')[1]
    dump(session, open(sessionfile, 'w'))
    #getfleet().save()
    args = []
    if len(sys.argv) > 1:
        os.execl(sys.argv[0], sys.argv[1], '-r', sessionfile, *sys.argv[1:])
    else:
        os.execl(sys.argv[0], '-r', sessionfile)
