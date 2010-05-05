# commonplugs/jsondata.py
#
#

""" 
    expose data through the jsonserver plugin. this is done by adding a 
    "public" attribute on the data. 

"""

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persist import Persist
from gozerlib.utils.exception import handle_exception
from gozerlib.datadir import datadir

## basic imports

import os
import logging

## commands

def handle_public(bot, event):
    if not event.rest:
        event.reply("<data path>")
        return
    path = datadir + os.sep + event.args[0]
    logging.warning("attempting to make %s public" % path)
    try:
        p = Persist(path)
        if p.data:
            p.data.public = True
            p.save()
            event.reply("%s is now made public." % path)
            return
    except Exception, ex:
        handle_exception()

    event.reply("can't find %s data" % path)

cmnds.add('public', handle_public, 'OPER')
examples.add('public', 'set a data file accessible through the jsonserver plugin', "public karma")

def handle_local(bot, event):
    if not event.rest:
        event.reply("<data path>")
        return
    path = datadir + os.sep + event.args[0]
    logging.warning("attempting to make %s local" % path)
    try:
        p = Persist(path)
        if p.data:
            p.data.public = False
            p.save()
            event.reply("%s is now made local." % path)
            return
    except Exception, ex:
        handle_exception()

    event.reply("can't find %s data" % path)

cmnds.add('local', handle_local, 'OPER')
examples.add('local', 'remove a data file from being accessible through the jsonserver plugin', "local karma")
