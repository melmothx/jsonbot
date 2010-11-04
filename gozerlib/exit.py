# gozerlib/exit.py
#
#

""" gozerlib's finaliser """

## gozerlib imports

from utils.trace import whichmodule
from plugins import plugs
from fleet import fleet
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
    defaultrunner.stop()
    cmndrunner.stop()
    sys.stdout.write("\n")
    logging.error('shutting down'.upper())
    try:os.remove('gozerlib.pid')
    except: pass
    logging.info('shutting down fleet')
    fleet.exit()
    logging.info('shutting down plugins')
    plugs.exit()
    logging.info('done')
    print "ltrs!"
    os._exit(0)

try: import google
except ImportError: atexit.register(globalshutdown)
