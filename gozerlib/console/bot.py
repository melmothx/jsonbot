# gozerlib/console/bot.py
#
#

""" console bot. """

## gozerlib imports

from gozerlib.socklib.utils.generic import waitforqueue
from gozerlib.errors import NoSuchCommand, NoInput
from gozerlib.botbase import BotBase
from gozerlib.exit import globalshutdown
from gozerlib.utils.exception import handle_exception
from event import ConsoleEvent

## basic imports

import time
import Queue
import logging
import sys

## classes

class ConsoleBot(BotBase):

    def start(self):
        time.sleep(0.1)
        while 1: 
            try: 
                input = raw_input("> ")
                event = ConsoleEvent()
                event.parse(self, input)

                try:
                    result = self._plugs.dispatch(self, event)
                    logging.debug("console - waiting for %s to finish" % event.usercmnd)
                    waitforqueue(result.outqueue)
                except NoSuchCommand:
                    print "no such command: %s" % event.usercmnd

            except NoInput:
                continue
            except (KeyboardInterrupt, EOFError):
                globalshutdown()
            except Exception, ex:
                handle_exception()
                

    def say(self, printto, txt, *args, **kwargs):
        self._raw(txt)

    def _raw(self, txt):
        sys.stdout.write("=> ")
        sys.stdout.write(txt)
        sys.stdout.write('\n')
