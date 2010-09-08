# gozerlib/tick.py
#
#

""" provide system wide clock tick. """

## gozerlib imports

from gozerlib.threadloop import TimedLoop
from gozerlib.eventbase import EventBase
from gozerlib.callbacks import callbacks

## classes

class TickLoop(TimedLoop):

    event = EventBase()
    event.type = event.cbtype = 'TICK'

    def start(self, bot=None):
        self.bot = bot
        TimedLoop.start(self)

    def handle(self):
        callbacks.check(self.bot, self.event)

tickloop = TickLoop('tickloop', 10)
