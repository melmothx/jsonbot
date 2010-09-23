# gozerlib/plugs/userstate.py
#
#

""" userstate is stored in jsondata/state/users/<username>. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persiststate import UserState
from gozerlib.errors import NoSuchUser

## userstate command

def handle_userstate(bot, ievent):
    """ let the user manage its own state. """
    try: (item, value) = ievent.args
    except ValueError: item = value = None
    username = bot.users.getname(ievent.userhost)
    if not username:
        ievent.reply("we have not state of %s" % ievent.userhost)
        return
    userstate = UserState(username)
    if item and value:
        userstate[item] = value
        userstate.save()
    result = []
    for i, j in userstate.data.iteritems(): result.append("%s=%s" % (i, j))
    if result: ievent.reply("userstate of %s: " % username, result)
    else: ievent.reply('no userstate of %s known' % username)

cmnds.add('userstate', handle_userstate, 'USER')
examples.add('userstate', 'get or set userstate', '1) userstate 2) userstate TZ -1')

## userstate-get command

def handle_userstateget(bot, ievent):
    """ get state of a user. """
    if not ievent.rest:
        ievent.missing('<username>')
        return
    userstate = UserState(ievent.rest)
    result = []
    for i, j in userstate.data.iteritems(): result.append("%s=%s" % (i, j))
    if result: ievent.reply("userstate of %s: " % ievent.rest, result)
    else: ievent.reply('no userstate of %s known' % ievent.rest)

cmnds.add('userstate-get', handle_userstateget, 'OPER')
examples.add('userstate-get', 'get the userstate of another user', 'userstate-get dunker')

## unset command

def handle_unset(bot, ievent):
    """ remove value from user state of the user giving the command. """
    try:
        item = ievent.args[0]
    except IndexError:
        ievent.missing('<item>')
        return
    username = bot.users.getname(ievent.userhost)
    if not username:
        ievent.reply("we have no state of you")
        return    
    userstate = UserState(username)
    try: del userstate.data[item]
    except KeyError:
        ievent.reply('no such item')
        return
    userstate.save()
    ievent.reply('item %s deleted' % item)

cmnds.add('unset', handle_unset, 'USER')
examples.add('unset', 'delete userstate variable for user gving the command', '1) unset TZ')
