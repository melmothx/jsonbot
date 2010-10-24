# gozerlib/plugs/dispatch.py
#
#

""" base class for all bots. """

## gozerlib imports

from gozerlib.callbacks import last_callbacks
from gozerlib.errors import NoSuchCommand

## basic logging

import logging
import copy

## defines

cpy = copy.deepcopy


## dispatch precondition

def predispatch(bot, event):
    if event.status == "done":
        logging.debug("dispatch - event is done .. ignoring")
        return
    if event.isremote():
        logging.done("dispatch - event is remote .. not dispatching")
        return
    return True

## dispatch callback

def dispatch(bot, event):
    """ dispatch an event. """
    if event.nodispatch:
        logging.debug("dispatch - nodispatch option is set - ignoring %s" % event.userhost)
        return
    bot.status = "dispatch"
    event.bind(bot)
    bot.curevent = event
    go = False
    try:
        execstr = event.iscmnd()
        if execstr:
            e = cpy(event)
            e.usercmnd = execstr.split()[0]
            e.txt = execstr
            e.showexception = True
            if not e.options: e.makeoptions()
            else: e.prepare()
            if e.usercmnd in event.chan.data.silentcommands: e.silent = True
            result = bot.plugs.dispatch(bot, e)
        else:
            logging.debug("dispatch - no go for %s (cc is %s)" % (event.auth or event.userhost, execstr))
            result =  []
    except NoSuchCommand:
        logging.info("no such command: %s" % event.usercmnd)
        result = []
    return result

## register callback

last_callbacks.add('PRIVMSG', dispatch, predispatch)
last_callbacks.add('MESSAGE', dispatch, predispatch)
last_callbacks.add('BLIP_SUBMITTED', dispatch, predispatch)
last_callbacks.add('WEB', dispatch, predispatch)
last_callbacks.add('CONSOLE', dispatch, predispatch)
last_callbacks.add('DCC', dispatch, predispatch)
last_callbacks.add('DISPATCH', dispatch, predispatch)
