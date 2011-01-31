# jsb/plugs/userstate.py
#
#

""" userstate is stored in jsondata/state/users/<username>. """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persiststate import UserState
from jsb.lib.errors import NoSuchUser

## set command

def handle_set(bot, ievent):
    """ let the user manage its own state. """
    try: (item, value) = ievent.args
    except ValueError: ievent.missing("<item> <value>") ; return
    ievent.user.state.data[item] = value
    ievent.user.state.save()
    ievent.reply("%s set to %s" % (item, value))
    
cmnds.add('set', handle_set, ['OPER', 'USER', 'GUEST'])
examples.add('set', 'set userstate', 'set place heerhugowaard')

## get command

def handle_get(bot, ievent):
    """ get state of a user. """
    target = ievent.rest
    userstate = ievent.user.state
    result = []
    for i, j in userstate.data.iteritems():
        if target == i or not target: result.append("%s=%s" % (i, j))
    if result: ievent.reply("state: ", result)
    else: ievent.reply('no userstate of %s known' % ievent.userhost)

cmnds.add('get', handle_get, ['OPER', 'USER', 'GUEST'])
examples.add('get', 'get your userstate', 'get')

## unset command

def handle_unset(bot, ievent):
    """ remove value from user state of the user giving the command. """
    try:
        item = ievent.args[0]
    except IndexError:
        ievent.missing('<item>')
        return
    try: del ievent.user.state.data[item]
    except KeyError:
        ievent.reply('no such item')
        return
    ievent.user.state.save()
    ievent.reply('item %s deleted' % item)

cmnds.add('unset', handle_unset, ['USER', 'GUEST'])
examples.add('unset', 'delete variable from your state', 'unset TZ')
