# jsb/plugs/dispatch.py
#
#

""" base class for all bots. """

## jsb imports

from jsb.lib.callbacks import last_callbacks
from jsb.lib.errors import NoSuchCommand

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
    if event.userhost in bot.ignore: logging.warn("%s - ignore on %s" % (bot.name, event.userhost)) ; return
    if event.nodispatch:
        logging.debug("dispatch - nodispatch option is set - ignoring %s" % event.userhost)
        return
    bot.status = "dispatch"
    event.bind(bot)
    bot.curevent = event
    go = False
    execstr = event.iscmnd()
    try:
        if execstr:
            event.iscommand = True
            e = cpy(event)
            e.usercmnd = execstr.split()[0]
            e.txt = execstr
            e.showexception = True
            if not e.options: e.makeoptions()
            e.prepare()
            if e.usercmnd in event.chan.data.silentcommands: e.silent = True
            result = bot.plugs.dispatch(bot, e)
            #event.leave()
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
last_callbacks.add('CMND', dispatch, predispatch)
