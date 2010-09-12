# gozerlib/botbase.py
#
#

""" base class for all bots. """

## gozerlib imports

from gozerlib.callbacks import last_callbacks
from gozerlib.errors import NoSuchCommand

## basic logging

import logging

## dispatch callback


def predispatch(bot, event):
    #logging.debug(u"predispatch: %s" % unicode(event.dump()))
    if event.status == "done":
        logging.debug("botbase - event is done .. ignoring")
        return
    if event.ttl <= 0:
        logging.debug("botbase - ttl of event is 0 .. ignoring")
        return
    if event.isremote:
        logging.warn("event is remote .. not dispatching")
        return
    return True

def dispatch(bot, event):
    """ dispatch an event. """

    bot.status = "dispatch"
    bot.curevent = event
    go = False

    try:
        execstr = event.iscmnd()
        if execstr:
            event.usercmnd = execstr.split()[0]
            event.txt = execstr
            event.finish()
            result = bot.plugs.dispatch(bot, event)
        else:
            logging.debug("dispatch - no go for %s (cc is %s)" % (event.userhost, execstr))
            result =  []
    except NoSuchCommand:
        logging.info("no such command: %s" % event.usercmnd)
        #event.reply("no such command: %s" % event.usercmnd)
        result = []

    return result

last_callbacks.add('PRIVMSG', dispatch, predispatch)
last_callbacks.add('MESSAGE', dispatch, predispatch)
last_callbacks.add('BLIP_SUBMITTED', dispatch, predispatch)
last_callbacks.add('WEB', dispatch, predispatch)
last_callbacks.add('CONSOLE', dispatch, predispatch)
last_callbacks.add('DCC', dispatch, predispatch)
last_callbacks.add('DISPATCH', dispatch, predispatch)
