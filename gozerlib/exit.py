# gozerlib/exit.py
#
#

""" gozerlib's finaliser """

## gozerlib imports

from utils.trace import whichmodule
#from eventhandler import mainhandler
from plugins import plugs
from fleet import fleet
from runner import defaultrunner
from gozerlib.config import cfg as config

## basic imports

import atexit
import os
import time
import sys
import logging

def globalshutdown():
    """ shutdown the bot. """
    sys.stdout.write("\n")
    logging.warning('shutting down')

    try:
        os.remove('gozerlib.pid')
    except:
        pass

    defaultrunner.stop()
    logging.info('shutting down fleet')
    fleet.exit()
    logging.info('shutting down plugins')
    plugs.exit()
    logging.info('done')
    sys.stdin.close()
    print "ltrs!"
    sys.stdout.close()
    os._exit(0)

try:
    import google
except ImportError:
    atexit.register(globalshutdown)
