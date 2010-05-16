# gozerlib/plugs/nickcapture.py
#
#

""" nick recapture callback. """

## gozerlib imports

from gozerlib.callbacks import callbacks

## callbacks

def ncaptest(bot, ievent):
    """ test if user is splitted. """
    if '*.' in ievent.txt or bot.server in ievent.txt:
        return 0
    if bot.orignick.lower() == ievent.nick.lower():
        return 1
    return 0

def ncap(bot, ievent):
    """ recapture the nick. """
    bot.donick(bot.orignick)

callbacks.add('QUIT', ncap, ncaptest, threaded=True)
