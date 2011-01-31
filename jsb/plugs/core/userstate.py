# jsb/plugs/userstate.py
#
#

""" userstate is stored in jsondata/state/users/<username>. """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persiststate import UserState
from jsb.lib.errors import NoSuchUser

## userstate command

def handle_set(bot, ievent):
    """ let the user manage its own state. """
    try: (item, value) = ievent.args
    except ValueError: ievent.missing("<item> <value>") ; return
    username = bot.users.getname(ievent.userhost)
    if not username:
        ievent.reply("we have not state of %s" % ievent.userhost)
        return
    userstate = UserState(username)
    userstate[item] = value
    userstate.save()
    ievent.reply("%s set to %s" % (item, value))
    
cmnds.add('set', handle_set, ['OPER', 'USER', 'GUEST'])
examples.add('set', 'set userstate', 'set place heerhugowaard')

## userstate-get command

def handle_get(bot, ievent):
    """ get state of a user. """
    target = ievent.rest
    username = ievent.user.data.name
    if not username: ievent.reply("we dont have any state of you.")
    userstate = UserState(username)
    result = []
    for i, j in userstate.data.iteritems():
        if target == i or not target: result.append("%s=%s" % (i, j))
    if result: ievent.reply("state: ", result)
    else: ievent.reply('no userstate of %s known' % username)

cmnds.add('get', handle_get, ['OPER', 'USER', 'GUEST'])
examples.add('get', 'get your userstate', 'get')

def handle_userstateget(bot, ievent):
    """ get state of a user. """
    if not ievent.rest: ievent.missing("<username>") ; return
    else: username = ievent.rest
    userstate = UserState(username)
    result = []
    for i, j in userstate.data.iteritems(): result.append("%s=%s" % (i, j))
    if result: ievent.reply("userstate of %s: " % username, result)
    else: ievent.reply('no userstate of %s known' % username)

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

cmnds.add('unset', handle_unset, ['USER', 'GUEST'])
examples.add('unset', 'delete variable from your state', 'unset TZ')
