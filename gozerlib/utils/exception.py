# gozerlib/utils/exception.py
#
#

""" exception related functions. """

## basic imports

import sys
import traceback
import logging
import thread
import os
import logging

## define

exceptionlist = []
exceptionevents = []

## functions

def exceptionmsg():
    """ create exception message as a string. """
    exctype, excvalue, tb = sys.exc_info()
    trace = traceback.extract_tb(tb)
    result = ""

    for i in trace:
        fname = i[0]
        linenr = i[1]
        func = i[2]
        plugfile = fname[:-3].split(os.sep)
        mod = []

        for i in plugfile[::-1]:
            if i in ['gaeupload', 'jsonbot']:
                break
            mod.append(i)
            if i in ['gozerlib', 'waveapi', 'google', 'gozerdata']:
                break

        ownname = '.'.join(mod[::-1])
        result += "%s:%s %s | " % (ownname, linenr, func)

    del trace
    res = "%s%s: %s" % (result, exctype, excvalue)

    if res not in exceptionlist:
        exceptionlist.append(res)

    return res

def handle_exception(event=None, log=True, txt=""):
    """ handle exception.. for now only print it. """
    errormsg = exceptionmsg()

    if txt:
        errormsg = "%s - %s" % (txt, errormsg)

    if log:
        logging.error(errormsg)

    if event:
        exceptionevents.append((event, errormsg))
        if event.bot:
            event.bot.error = errormsg
            event.reply(errormsg)
