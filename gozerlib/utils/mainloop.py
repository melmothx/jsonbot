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
            time.sleep(1)
            mainhandler.handle_one()
        except KeyboardInterrupt:
            break
        except Exception, ex:
            handle_exception()
            globalshutdown()
            os._exit(1)

    globalshutdown()
    os._exit(0)
