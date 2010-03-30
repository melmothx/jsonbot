# gozerbot/monitor.py
#
#

""" monitors .. call callback on bot output. """

## gozerlib import s

from gozerlib.monitor import Monitor

## gozerlib.socket.irc imports

from ircevent import Ircevent

## classes

class Outmonitor(Monitor):

    """ monitor for bot output (bot.send). """

    def handle(self, bot, txt):

        """ fire outmonitor callbacks. """

        ievent = Ircevent().parse(bot, txt)

        if not ievent:
            rlog(10, 'monitor', "can't make ircevent: %s" % txt)
            return

        ievent.nick = bot.nick

        try:
            ievent.userhost = bot.userhosts.data[bot.nick]
        except (KeyError, AttributeError):
            ievent.userhost = "bot@bot"

        Monitor.handle(self, bot, ievent)

# bot.send() monitor
outmonitor = Outmonitor('outmonitor') 

# bot.say() monitor
saymonitor = Monitor('saymonitor')
