# gozerlib/console/bot.py
#
#

""" console bot. """

## gozerlib imports

from gozerlib.datadir import datadir
from gozerlib.socklib.utils.generic import waitforqueue
from gozerlib.errors import NoSuchCommand, NoInput
from gozerlib.botbase import BotBase
from gozerlib.exit import globalshutdown
from gozerlib.utils.generic import strippedtxt
from gozerlib.utils.exception import handle_exception
from gozerlib.fleet import fleet
from event import ConsoleEvent

## basic imports

import time
import Queue
import logging
import sys
import code
import os
import readline
import atexit
import getpass

## defines

histfilepath = os.path.expanduser(datadir + os.sep + "run" + os.sep + "console-history")

## classes

class HistoryConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>",
                 histfile=histfilepath):
        self.fname = histfile
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)

    def init_history(self, histfile):
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            #atexit.register(self.save_history, histfile)

    def save_history(self, histfile=None):
        readline.write_history_file(histfile or self.fname)

console = HistoryConsole()

class ConsoleBot(BotBase):

    def __init__(self, cfg=None, users=None, plugs=None, botname=None, *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        self.type = "console"
        self.nick = botname or "console"

    def start(self):
        time.sleep(0.1)
        print "bot nick is %s" % self.nick
        while 1: 
            try: 
                input = console.raw_input("> ")
                event = ConsoleEvent()
                event.parse(self, input, console)
                if False and input.startswith('#'):
                    try:
                        env = {"bot": self, "event": event}
                        env.update(locals())
                        env.update(globals())
                        console.locals.update(env)
                        console.runsource(input[1:])
                        continue
                    except Exception, ex:
                        handle_exception()
                        continue
                try:
                    result = self.doevent(event)
                    if not result:
                            continue
                    logging.debug("console - waiting for %s to finish" % event.usercmnd)
                    waitforqueue(result.outqueue)
                except NoSuchCommand:
                    print "no such command: %s" % event.usercmnd

            except NoInput:
                continue
            except (KeyboardInterrupt, EOFError):
                break
            except Exception, ex:
                handle_exception()

        console.save_history()
        globalshutdown()
                

    def say(self, printto, txt, *args, **kwargs):
        if not txt:
            logging.warn("console - %s - no txt provided" % printto)
            return
        if getpass.getuser() == printto:
            self._raw(strippedtxt(txt))
            self.outmonitor(self.name, printto, txt)

    def _raw(self, txt):
        sys.stdout.write("=> ")
        sys.stdout.write(txt)
        sys.stdout.write('\n')
