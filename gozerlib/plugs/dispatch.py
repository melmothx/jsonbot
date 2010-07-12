# gozerlib/botbase.py
#
#

""" base class for all bots. """

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.errors import NoSuchCommand

## basic logging

import logging

## dispatch callback

if True:

    def predispatch(bot, event):
        #logging.debug(u"predispatch: %s" % unicode(event.dump()))
        if event.status == "done":
            logging.debug("botbase - event is done .. ignoring")
            return
        if event.ttl <= 0:
            logging.debug("botbase - ttl of event is 0 .. ignoring")
            return
        if event.isremote and not event.remotecmnd:
            logging.debug("event is remote but not command .. not dispatching")
            return
        return True

    def dispatch(bot, event):
        """ dispatch an event. """

        bot.status = "dispatch"
        bot.curevent = event
        go = False
        cc = "!"

        if event.chan:
            cc = event.chan.data.cc
        if not cc:
            cc = "!"

        logging.debug("cc for %s is %s (%s)" % (event.title or event.channel or event.userhost, cc, bot.nick))
        matchnick = unicode(bot.nick + u":")
        #logging.debug("dispatch - %s" % event.txt)        

        if event.txt and event.txt[0] in cc:
            event.txt = event.txt[1:]
            if event.txt:
                event.usercmnd = event.txt.split()[0]
            else:
                event.usercmnd = None
            event.makeargs()
            go = True
        elif event.txt.startswith(matchnick):
            event.txt = event.txt[len(matchnick) + 1:]
            if event.txt:
                event.usercmnd = event.txt.split()[0]
            else:
                event.usercmnd = None
            event.makeargs()
            go = True

        try:
            if go:
                event.finish()
                result = bot.plugs.dispatch(bot, event)
                event.leave()
            else:
                logging.debug("dispatch - no go for %s (%s)" % (event.txt, event.userhost))
                result =  []
        except NoSuchCommand:
            logging.info("no such command: %s" % event.usercmnd)
            event.leave()
            result = []

        return result


    callbacks.add('PRIVMSG', dispatch, predispatch)
    callbacks.add('MESSAGE', dispatch, predispatch)
    callbacks.add('BLIP_SUBMITTED', dispatch, predispatch)
    callbacks.add('WEB', dispatch, predispatch)
    callbacks.add('CONSOLE', dispatch, predispatch)
