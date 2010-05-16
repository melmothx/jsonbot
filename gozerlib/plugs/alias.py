# gozerlib/plugs/alias.py
#
#

""" this alias plugin allows aliases for commands to be added. aliases are in
    the form of <alias> -> <command> .. aliases to aliases are not allowed, 
    aliases are per user.
"""

## gozerbot imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.datadir import datadir
from gozerlib.persiststate import UserState

## basic imports

import os

def handle_aliassearch(bot, ievent):
    """ alias-search <what> .. search aliases. """
    try:
        what = ievent.args[0]
    except IndexError:
        ievent.missing('<what>')
        return

    result = []
    res = []
    aliases = ievent.userstate.data.aliases
    for i, j in aliases.iteritems():
        if what in i or what in j:
            result.append((i, j))

    if not result:
        ievent.reply('no %s found' % what)
    else:
        for i in result:
            res.append("%s => %s" % i)
        ievent.reply("aliases matching %s: " % what, res)

cmnds.add('alias-search', handle_aliassearch, 'USER')
examples.add('alias-search', 'search aliases',' alias-search web')

def handle_aliasset(bot, ievent):
    """ alias-set <from> <to> .. set alias. """
    try:
        (aliasfrom, aliasto) = (ievent.args[0], ' '.join(ievent.args[1:]))
    except IndexError:
        ievent.missing('<from> <to>')
        return
    if not aliasto:
        ievent.missing('<from> <to>')
        return
    if cmnds.has_key(aliasfrom):
        ievent.reply('command with same name already exists.')
        return

    # add alias and save
    aliases = ievent.userstate.data.aliases
    if not aliases:
        ievent.userstate.data.aliases = aliases = {}
    if aliases.has_key(aliasto):
        ievent.reply("can't alias an alias")
        return
    ievent.userstate.data.aliases[aliasfrom] = aliasto
    ievent.userstate.save()
    ievent.reply('alias added')

cmnds.add('alias', handle_aliasset, 'USER', allowqueue=False)
examples.add('alias', 'alias <alias> <command> .. define alias', 'alias ll list')

def handle_delalias(bot, ievent):
    """ alias-del <word> .. delete alias. """
    try:
        what = ievent.args[0]
    except IndexError:
        ievent.missing('<what>')
        return

    # del alias and save
    aliases = ievent.userstate.data.aliases
    try:
        del aliases[what]
        ievent.userstate.save()
        ievent.reply('alias deleted')
    except KeyError:
        ievent.reply('there is no %s alias' % what)

cmnds.add('alias-del', handle_delalias, 'USER')
examples.add('alias-del', 'alias-del <what> .. delete alias', 'alias-del ll')

def handle_getaliases(bot, ievent):
    """ aliases .. show aliases. (per user) """
    aliases = ievent.userstate.data.aliases
    ievent.reply("aliases: %s" % str(aliases))

cmnds.add('aliases', handle_getaliases, 'USER')
examples.add('aliases', 'aliases <what> .. get aliases', 'aliases')
