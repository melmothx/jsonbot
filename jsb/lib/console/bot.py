# jsb/console/bot.py
#
#

""" console bot. """

## jsb imports

from jsb.lib.datadir import getdatadir
from jsb.utils.generic import waitforqueue
from jsb.lib.errors import NoSuchCommand, NoInput
from jsb.lib.botbase import BotBase
from jsb.lib.exit import globalshutdown
from jsb.utils.generic import strippedtxt, waitevents
from jsb.utils.exception import handle_exception
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
import re

## defines

histfilepath = os.path.expanduser(getdatadir() + os.sep + "run" + os.sep + "console-history")

## HistoryConsole class

class HistoryConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", histfile=histfilepath):
        self.fname = histfile
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)

    def init_history(self, histfile):
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try: readline.read_history_file(histfile)
            except IOError: pass

    def save_history(self, histfile=None):
        readline.write_history_file(histfile or self.fname)

## the console

console = HistoryConsole()

## ConsoleBot

class ConsoleBot(BotBase):

    ERASE_LINE = '\033[2K'
    BOLD='\033[1m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'


    def __init__(self, cfg=None, users=None, plugs=None, botname=None, *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        self.type = "console"
        self.nick = botname or "console"

    def startshell(self, connect=True):
        """ start the console bot. """
        self.start(False)
        time.sleep(0.1)
        self.dostart()
        while not self.stopped: 
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
                    #event.direct = True
                self.put(event)
                waitevents([event, ])
                #if not result: continue
                #logging.debug("console - waiting for %s to finish" % event.usercmnd)
                #res = waitforqueue(event.outqueue)
                time.sleep(0.2)
                #logging.debug("console - %s" % res)
            except NoInput: continue
            except (KeyboardInterrupt, EOFError): break
            except Exception, ex: handle_exception()
        console.save_history()


    def outnocb(self, printto, txt, *args, **kwargs):
        txt = self.normalize(txt)
        self._raw(txt)         

    def _raw(self, txt):
        """ do raw output to the console. """
        logging.info("%s - out - %s" % (self.name, txt))             
        sys.stdout.write(txt)
        sys.stdout.write('\n')

    def action(self, channel, txt):
        txt = self.normalize(txt)
        self._raw(txt)

    def notice(self, channel, txt):
        txt = self.normalize(txt)
        self._raw(txt)

    def exit(self):
        """ called on exit. """
        console.save_history()

    def normalize(self, what):
        what = strippedtxt(what)
        what = what.replace("<b>", self.GREEN)
        what = what.replace("</b>", self.ENDC)
        what = what.replace("&lt;b&gt;", self.GREEN)
        what = what.replace("&lt;/b&gt;", self.ENDC)
        if what.count(self.ENDC) % 2: what = "%s%s" %  (self.ENDC, what)
        return what
