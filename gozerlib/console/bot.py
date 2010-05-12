# gozerlib/console/bot.py
#
#

""" console bot. """

## gozerlib imports

from gozerlib.errors import NoSuchCommand
from gozerlib.botbase import BotBase
from gozerlib.exit import globalshutdown
from event import ConsoleEvent

## basic imports

import time

## classes

class ConsoleBot(BotBase):

    def start(self):
        time.sleep(0.1)
        input = raw_input("> ")
        while 1: 
            try: 
                if len(input) > 1:
                    event = ConsoleEvent()
                    event.parse(input)

                    try:
                        result = self.plugs.dispatch(self, event)
                    except NoSuchCommand:
                        print "no such command: %s" % event.usercmnd

                    time.sleep(0.1)
                    input = raw_input("> ")

            except (KeyboardInterrupt, EOFError):
                globalshutdown()
