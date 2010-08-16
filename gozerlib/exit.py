# gozerlib/exit.py
#
#

""" gozerlib's finaliser """

## gozerlib imports

from utils.trace import whichmodule
#from eventhandler import mainhandler
from plugins import plugs
from fleet import fleet
from runner import runners_stop
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
    logging.info('shutting down')

    try:
        os.remove('gozerlib.pid')
    except:
        pass

    runners_stop()
    logging.info('shutting down fleet')
    fleet.exit()
    logging.info('shutting down plugins')
    plugs.exit()
    logging.info('done')
    #sys.stdin.close()
    #sys.stdout.close()
    print "ltrs!"
    os._exit(0)

try:
    import google
except ImportError:
    atexit.register(globalshutdown)
