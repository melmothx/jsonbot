# commonplugs/controlchar.pu
#
#

"""
     command to control the control (command) characters. The cc is a string 
    containing the allowed control characters.

"""

from gozerlib.commands import cmnds
from gozerlib.examples import examples

def handle_cc(bot, ievent):

    """ cc [<controlchar>] .. set/get control character of channel. """

    try:
        what = ievent.args[0]

        if not bot.users.allowed(ievent.userhost, 'OPER'):
            return

        if len(what) > 1:
            ievent.reply("only one character is allowed")
            return

        try:
            ievent.chan.data.cc = what
        except (KeyError, TypeError):
            ievent.reply("no channel %s in database" % chan)
            return

        ievent.chan.save()
        ievent.reply('control char set to %s' % what)
    except IndexError:
        # no argument given .. show cc of channel command is given in
        try:
            cchar = ievent.chan.data.cc
            ievent.reply('control character(s) for channel %s are/is %s' % (ievent.channel, cchar))
        except (KeyError, TypeError):
            ievent.reply("default cc is %s" % bot.cfg['defaultcc'])

cmnds.add('cc', handle_cc, 'USER')
examples.add('cc', 'set control char of channel or show control char of channel','1) cc ! 2) cc')

def handle_ccadd(bot, ievent):

    """ add a control char to the channels cc list. """

    try:
        what = ievent.args[0]

        if not bot.users.allowed(ievent.userhost, 'OPER'):
            return

        if len(what) > 1:
            ievent.reply("only one character is allowed")
            return

        try:
            ievent.chan.data.cc += what
        except (KeyError, TypeError):
            ievent.reply("no channel %s in database" % ievent.channel)
            return

        ievent.chan.save()
        ievent.reply('control char %s added' % what)
    except IndexError:
        ievent.missing('<cc> [<channel>]')

cmnds.add('cc-add', handle_ccadd, 'OPER', allowqueue=False)
examples.add('cc-add', 'cc-add <control char> .. add control character', 'cc-add #')

def handle_ccdel(bot, ievent):

    """ remove a control char from the channels cc list. """

    try:
        what = ievent.args[0]

        if not bot.users.allowed(ievent.userhost, 'OPER'):
            return

        if len(what) > 1:
            ievent.reply("only one character is allowed")
            return

        if ievent.chan.data.cc:
            ievent.chan.data.cc = ievent.chan.data.cc.replace(what, '')
            ievent.chan.save()

        ievent.reply('control char %s deleted' % what)

    except IndexError:
        ievent.missing('<cc> [<channel>]')

cmnds.add('cc-del', handle_ccdel, 'OPER')
examples.add('cc-del', 'cc-del <control character> .. remove cc', 'cc-del #')
