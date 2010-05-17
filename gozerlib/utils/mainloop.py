# gozerlib/utils/mainloop.py
#
#

""" main loop used in jsonbot binairies. """

## gozerlib imports

from gozerlib.eventhandler import mainhandler
from gozerlib.exit import globalshutdown

## basic imports

import os
import time

## functions

def mainloop():
    while 1:
        try:
            time.sleep(0.01)
            mainhandler.handle_one()
        except KeyboardInterrupt:
            globalshutdown()
            os._exit(0)
        except Exception, ex:
            handle_exception()
            globalshutdown()
            os._exit(1)
