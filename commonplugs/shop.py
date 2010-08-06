# plugs/shop.py
#
#

""" maitain a shopping list (per user). """

## gozerlib imports

from gozerlib.utils.generic import getwho, jsonstring
from gozerlib.users import users
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.datadir import datadir
from gozerlib.utils.pdol import Pdol

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

    sayshop(bot, ievent, ievent.user.data.shops)

cmnds.add('shop', handle_shop, ['USER', 'GUEST'])

def handle_shop2(bot, ievent):
    """ add items to shop list """
    if not ievent.rest:
        ievent.missing('<shopitem>')
        return
    else:
        what = ievent.rest
    if not ievent.user.data.shops:
        ievent.user.data.shops = []
    ievent.user.data.shops.append(what)
    ievent.user.save()
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
        shop = ievent.user.data.shops
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
    ievent.user.save()
    ievent.reply('%s shop item(s) deleted' % teller)

cmnds.add('got', handle_got, ['USER', 'GUEST'])
examples.add('got', 'got <listofnrs> .. remove item <listofnrs> from shop list','1) got 3 2) got 1 6 8')

