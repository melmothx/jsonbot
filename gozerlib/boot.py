# gozerlib/boot.py
#
#

""" admin related data and functions. """

## gozerlib imports

from gozerlib.persist import Persist
from gozerlib.datadir import datadir
import users

## basic imports

import logging
import os
import sys

#sys.path.insert(0, os.getcwd())

## defines

try:
    import waveapi
    plugin_packages = ['gozerlib.plugs', 'gozerlib.gae.plugs', 'commonplugs', 'jsondir.myplugs', 'waveplugs']
except ImportError:
    plugin_packages = ['gozerlib.plugs', 'gozerlib.gae.plugs', 'commonplugs', 'jsondir.myplugs', 'waveplugs', 'socketplugs']

default_plugins = ['gozerlib.plugs.admin', 'gozerlib.plugs.outputcache']

# these are set in gozerlib/boot.py

loaded = False
cmndtable = None 
pluginlist = None
callbacktable = None

rundir = datadir + os.sep + "run"

## functions

def boot(force=False):
    """ initialize the bot. """
    global loaded
    logging.warn("boot - starting ..")

    global cmndtable
    if not cmndtable:
        cmndtable = Persist(rundir + os.sep + 'cmndtable')
    global pluginlist
    if not pluginlist:
         pluginlist = Persist(rundir + os.sep + 'pluginlist')
    global callbacktable
    if not callbacktable:
         callbacktable = Persist(rundir + os.sep + 'callbacktable')
    
    from gozerlib.plugins import plugs
    if not cmndtable.data or force:
        plugs.loadall(plugin_packages)
        loaded = True
        savecmndtable()

    if not pluginlist.data or force:
        if not loaded:
            plugs.loadall(plugin_packages)
            loaded = True
        savepluginlist()

    if not callbacktable.data or force:
        if not loaded:
            plugs.loadall(plugin_packages)
            loaded = True
        savecallbacktable()

    if not loaded:
        for plug in default_plugins:
            plugs.load(plug)

    logging.warn("boot - booting done")

def savecmndtable():
    """ save command -> plugin list to db backend. """
    global cmndtable
    cmndtable.data = {}

    from gozerlib.commands import cmnds

    for cmndname, c in cmnds.iteritems():
        if cmndname:
            cmndtable.data[cmndname] = c.modname   

    if cmnds.subs:
        for cmndname, clist in cmnds.subs.iteritems():
            if cmndname:
                if clist and len(clist) == 1:
                    cmndtable.data[cmndname] = clist[0].modname   

    logging.debug("saving command table")
    cmndtable.save()

def getcmndtable():
    """ save command -> plugin list to db backend. """
    global cmndtable
    if not cmndtable:
        boot()

    return cmndtable.data

def savecallbacktable():
    """ save command -> plugin list to db backend. """
    global callbacktable
    callbacktable.data = {}
  
    from gozerlib.callbacks import callbacks

    for type, cbs in callbacks.cbs.iteritems():
        for c in cbs:
            if not callbacktable.data.has_key(type):
                callbacktable.data[type] = []
            callbacktable.data[type].append(c.modname)

    logging.debug("saving callback table")
    callbacktable.save()

def getcallbacktable():
    """ save command -> plugin list to db backend. """
    global callbacktable
    if not callbacktable:
        boot()

    return callbacktable.data

def savepluginlist():
    """ save a list of available plugins to db backend. """
    global pluginlist
    pluginlist.data = []

    from gozerlib.commands import cmnds

    for cmndname, c in cmnds.iteritems():
        if not c.plugname:
            logging.warn("boot - not adding %s to pluginlist" % cmndname)
            continue
        if c.plugname not in pluginlist.data:
            pluginlist.data.append(c.plugname)
    pluginlist.data.sort()
    logging.debug("saving plugin list")
    pluginlist.save()

def getpluginlist():
    """ get the plugin list. """
    global pluginlist
    if not pluginlist:
         boot()
    return pluginlist.data
