# gozerlib/console/bot.py
#
#

""" console bot. """

## gozerlib imports

from gozerlib.socklib.utils.generic import waitforqueue
from gozerlib.errors import NoSuchCommand
from gozerlib.botbase import BotBase
from gozerlib.exit import globalshutdown
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
        input = raw_input("> ")
        while 1: 
            try: 
                if len(input) > 1:
                    event = ConsoleEvent()
                    event.parse(self, input)

                    try:
                        result = self._plugs.dispatch(self, event)
                        logging.warn("plugins - waiting for %s to finish" % event.usercmnd)
                        waitforqueue(result.outqueue)
                    except NoSuchCommand:
                        print "no such command: %s" % event.usercmnd

                    time.sleep(0.1)
                    input = raw_input("> ")

            except (KeyboardInterrupt, EOFError):
                globalshutdown()


    def say(self, printto, txt, *args, **kwargs):
        self._raw(txt)

    def _raw(self, txt):
        sys.stdout.write("=> ")
        sys.stdout.write(txt)
        sys.stdout.write('\n')
