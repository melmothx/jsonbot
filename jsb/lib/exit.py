# jsb/exit.py
#
#

""" jsb's finaliser """

## jsb imports

from jsb.utils.trace import whichmodule
from plugins import plugs
from runner import defaultrunner, cmndrunner

## basic imports

import atexit
import os
import time
import sys
import logging

## functions

def globalshutdown():
    """ shutdown the bot. """
    logging.warn('shutting down'.upper())
    defaultrunner.stop()
    cmndrunner.stop()
    sys.stdout.write("\n")
    try:os.remove('jsb.pid')
    except: pass
    from fleet import getfleet
    fleet = getfleet()
    if fleet:
        logging.warn('shutting down fleet')
        fleet.exit()
    logging.warn('shutting down plugins')
    plugs.exit()
    logging.warn('done')
    #print "ltrs!"
    os._exit(0)

#try: import google
#except ImportError: atexit.register(globalshutdown)
