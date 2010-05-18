# gozerlib/boot.py
#
#

""" admin related data and functions. """

## gozerlib imports

from gozerlib.persist import Persist
from gozerlib.plugins import plugs
from gozerlib.commands import cmnds
from gozerlib.admin import plugin_packages, default_plugins
from gozerlib.callbacks import callbacks
from gozerlib.datadir import datadir
import admin
import users

## basic imports

import logging
import os
import sys

sys.path.insert(0, os.getcwd())

## define

rundir = datadir + os.sep + "run"

## functions

def boot(force=False):
    """ initialize the bot. """
    global loaded
    logging.info("boot - starting ..")

    if not admin.cmndtable:
        admin.cmndtable = Persist(rundir + os.sep + 'cmndtable')
    if not admin.pluginlist:
         admin.pluginlist = Persist(rundir + os.sep + 'pluginlist')
    if not admin.callbacktable:
         admin.callbacktable = Persist(rundir + os.sep + 'callbacktable')
    
    if not admin.cmndtable.data or force:
        plugs.loadall(plugin_packages)
        admin.loaded = True
        savecmndtable()

    if not admin.pluginlist.data or force:
        if not admin.loaded:
            plugs.loadall(plugin_packages)
            admin.loaded = True
        savepluginlist()

    if not admin.callbacktable.data or force:
        if not admin.loaded:
            plugs.loadall(plugin_packages)
            loaded = True
        savecallbacktable()

    if not admin.loaded:
        for plug in default_plugins:
            plugs.load(plug)

    logging.info("boot - booting done")

def savecmndtable():
    """ save command -> plugin list to db backend. """
    admin.cmndtable.data = {}

    for cmndname, c in cmnds.iteritems():
        if cmndname:
            admin.cmndtable.data[cmndname] = c.modname   

    if cmnds.subs:
        for cmndname, clist in cmnds.subs.iteritems():
            if cmndname:
                if clist and len(clist) == 1:
                    admin.cmndtable.data[cmndname] = clist[0].modname   

    logging.debug("saving command table")
    admin.cmndtable.save()

def getcmndtable():
    """ save command -> plugin list to db backend. """
    if not admin.cmndtable:
        boot()

    return admin.cmndtable.data

def savecallbacktable():
    """ save command -> plugin list to db backend. """
    admin.callbacktable.data = {}

    for type, cbs in callbacks.cbs.iteritems():
        for c in cbs:
            if not admin.callbacktable.data.has_key(type):
                admin.callbacktable.data[type] = []
            admin.callbacktable.data[type].append(c.plugname)

    logging.debug("saving callback table")
    admin.callbacktable.save()

def getcallbacktable():
    """ save command -> plugin list to db backend. """
    if not admin.callbacktable:
        boot()

    return admin.callbacktable.data

def savepluginlist():
    """ save a list of available plugins to db backend. """
    admin.pluginlist.data = []

    for cmndname, c in cmnds.iteritems():
        if not c.plugname:
            logging.warn("boot - not adding %s to pluginlist" % cmndname)
            continue
        if c.plugname not in admin.pluginlist.data:
            admin.pluginlist.data.append(c.plugname)
    admin.pluginlist.data.sort()
    logging.debug("saving plugin list")
    admin.pluginlist.save()

def getpluginlist():
    """ get the plugin list. """
    if not admin.pluginlist:
         boot()
    return admin.pluginlist.data
 