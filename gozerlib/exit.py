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
    logging.warning('shutting down')

    try:
        os.remove('gozerlib.pid')
    except:
        pass

    try:
        runners_stop()
        logging.debug('shutting down fleet')
        fleet.exit()
        logging.debug('shutting down plugins')
        plugs.exit()
        logging.warn('done')
        print "bye!"
        os._exit(0)

    except Exception, ex:
        logging.error('exit - error %s:' % str(ex))

atexit.register(globalshutdown)
