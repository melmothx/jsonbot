# plugs/shop.py
#
#

""" maitain a shopping list (per user). """

## jsb imports

from jsb.utils.generic import getwho, jsonstring
from jsb.lib.users import users
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.utils.pdol import Pdol

## basic imports

import os

## functions

def size():
    """ return number of shops entries """
    return len(shops.data)

def sayshop(bot, ievent, shoplist):
    """ output shoplist """
    if not shoplist:
        ievent.reply('nothing to shop ;]')
        return
    result = []
    teller = 0
    for i in shoplist:
        result.append('%s) %s' % (teller, i))
        teller += 1
    ievent.reply("shoplist: ", result, dot=" ")

## commands

def handle_shop(bot, ievent):
    """ shop [<item>] .. show shop list or add <item> """
    if len(ievent.args) != 0:
        handle_shop2(bot, ievent)
        return

    if ievent.user.state.data.shops:
        sayshop(bot, ievent, ievent.user.state.data.shops)
    else:
        ievent.reply("no shops")

cmnds.add('shop', handle_shop, ['USER', 'GUEST'])

def handle_shop2(bot, ievent):
    """ add items to shop list """
    if not ievent.rest:
        ievent.missing('<shopitem>')
        return
    else:
        what = ievent.rest
    if not ievent.user.state.data.shops:
        ievent.user.state.data.shops = []
    ievent.user.state.data.shops.append(what)
    ievent.user.state.save()
    ievent.reply('shop item added')

examples.add('shop', 'shop [<item>] .. show shop items or add a shop item', '1) shop 2) shop bread')

def handle_got(bot, ievent):
    """ got <listofnrs> .. remove items from shoplist """
    if len(ievent.args) == 0:
        ievent.missing('<list of nrs>')
        return
    try:
        nrs = []
        for i in ievent.args:
            nrs.append(int(i))
    except ValueError:
        ievent.reply('%s is not an integer' % i)
        return
    try:
        shop = ievent.user.state.data.shops
    except KeyError:
        ievent.reply('nothing to shop ;]')
        return
    if not shop:
        ievent.reply("nothing to shop ;]")
        return
    nrs.sort()
    nrs.reverse()
    teller = 0
    for i in range(len(shop)-1, -1 , -1):
        if i in nrs:
            try:
                del shop[i]
                teller += 1
            except IndexError:
                pass
    ievent.user.state.save()
    ievent.reply('%s shop item(s) deleted' % teller)

cmnds.add('got', handle_got, ['USER', 'GUEST'])
examples.add('got', 'got <listofnrs> .. remove item <listofnrs> from shop list','1) got 3 2) got 1 6 8')

