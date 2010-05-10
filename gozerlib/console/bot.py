# gozerlib/console/bot.py
#
#

""" console bot. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.botbase import BotBase
from gozerlib.exit import globalshutdown

## basic imports

import time
import getpass

class ConsoleBot(BotBase):

    def start(self):
        while 1: 
            try: 
                time.sleep(0.1)
                #sys.stdout.write("> ")
                input = raw_input("> ")

                if len(input) > 1:
                    event = EventBase()
                    event.auth = getpass.getuser()
                    event.userhost = event.auth   
                    event.txt = input
                    event.usercmnd = input.split()[0]
                    event.makeargs()

                    try:
                        result = self.plugs.dispatch(self, event)
                    except NoSuchCommand:
                        print "no such command: %s" % event.usercmnd

            except (KeyboardInterrupt, EOFError):
                globalshutdown()
