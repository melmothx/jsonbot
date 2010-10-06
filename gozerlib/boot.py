# gozerlib/boot.py
#
#

""" admin related data and functions. """

## gozerlib imports

from gozerlib.utils.generic import checkpermissions
from gozerlib.persist import Persist
from gozerlib.utils.exception import handle_exception
from gozerlib.datadir import datadir
import users

## basic imports

import logging
import os
import sys

## paths

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.getcwd() + os.sep + '..')

## defines

ongae = False
try:
    import waveapi
    plugin_packages = ['gozerlib.plugs', 'gaeplugs', 'commonplugs', 'gozerdata.myplugs', 'waveplugs']
    ongae = True
except ImportError: plugin_packages = ['gozerlib.plugs', 'gaeplugs', 'commonplugs', 'gozerdata.myplugs', 'waveplugs', 'socketplugs']

default_plugins = ['gozerlib.plugs.admin', 'gozerlib.plugs.dispatch']

# these are set in gozerlib/boot.py

loaded = False
cmndtable = None 
pluginlist = None
callbacktable = None

rundir = datadir + os.sep + "run"

## boot function

def boot(force=False, encoding="utf-8", umask=None):
    """ initialize the bot. """
    logging.info("booting ..")
    try:
        if os.getuid() == 0:
            print "don't run the bot as root"
            os._exit(1)
    except AttributeError: pass
    try:
        k = open(rundir + os.sep + 'jsonbot.pid','w')
        k.write(str(os.getpid()))
        k.close()
    except IOError: pass
    try:
        if not ongae:
            reload(sys)
            sys.setdefaultencoding(encoding)
    except (AttributeError, IOError): pass
    try:
        if not umask: checkpermissions('gozerdata', 0700) 
        else: checkpermissions('gozerdata', umask)  
    except: handle_exception()
    global loaded
    global cmndtable
    global pluginlist
    global callbacktable
    if not cmndtable: cmndtable = Persist(rundir + os.sep + 'cmndtable')
    if not pluginlist: pluginlist = Persist(rundir + os.sep + 'pluginlist')
    if not callbacktable: callbacktable = Persist(rundir + os.sep + 'callbacktable')
    from gozerlib.plugins import plugs
    if not cmndtable.data or force:
        plugs.loadall(plugin_packages, force=True)
        loaded = True
        savecmndtable()
    if not pluginlist.data or force:
        if not loaded:
            plugs.loadall(plugin_packages, force=True)
            loaded = True
        savepluginlist()
    if not callbacktable.data or force:
        if not loaded:
            plugs.loadall(plugin_packages, force=True)
            loaded = True
        savecallbacktable()
    if not loaded:
        logging.info("boot - plugins not loaded .. loading defaults")
        for plug in default_plugins:
            plugs.reload(plug)
    logging.warn("boot - done")

## commands related commands

def savecmndtable(modname=None):
    """ save command -> plugin list to db backend. """
    global cmndtable
    if not cmndtable.data: cmndtable.data = {}
    from gozerlib.commands import cmnds
    assert cmnds
    if cmnds.subs:
        for name, clist in cmnds.subs.iteritems():
            if name:
                if clist and len(clist) == 1: cmndtable.data[name] = clist[0].modname   
    for cmndname, c in cmnds.iteritems():
        if modname and c.modname != modname: continue
        if cmndname and c:
            cmndtable.data[cmndname] = c.modname   
    logging.warn("saving command table")
    assert cmndtable
    cmndtable.save()

def getcmndtable():
    """ save command -> plugin list to db backend. """
    global cmndtable
    if not cmndtable: boot()
    return cmndtable.data

## callbacks related commands

def savecallbacktable(modname=None):
    """ save command -> plugin list to db backend. """
    global callbacktable
    assert callbacktable
    if not callbacktable.data: callbacktable.data = {}
    from gozerlib.callbacks import first_callbacks, callbacks, last_callbacks, remote_callbacks
    for cb in [first_callbacks, callbacks, last_callbacks, remote_callbacks]:
        for type, cbs in cb.cbs.iteritems():
            for c in cbs:
                if modname and c.modname != modname: continue
                if not callbacktable.data.has_key(type): callbacktable.data[type] = []
                callbacktable.data[type].append(c.modname)
    logging.warn("saving callback table")
    assert callbacktable
    callbacktable.save()

def getcallbacktable():
    """ save command -> plugin list to db backend. """
    global callbacktable
    if not callbacktable: boot()
    return callbacktable.data

## plugin list related commands

def savepluginlist(modname=None):
    """ save a list of available plugins to db backend. """
    global pluginlist
    if not pluginlist.data: pluginlist.data = []
    from gozerlib.commands import cmnds
    assert cmnds
    for cmndname, c in cmnds.iteritems():
        if modname and c.modname != modname: continue
        if c and not c.plugname:
            logging.info("boot - not adding %s to pluginlist" % cmndname)
            continue
        if c and c.plugname not in pluginlist.data: pluginlist.data.append(c.plugname)
    pluginlist.data.sort()
    logging.warn("saving plugin list")
    assert pluginlist
    pluginlist.save()

def getpluginlist():
    """ get the plugin list. """
    global pluginlist
    if not pluginlist: boot()
    return pluginlist.data

## update_mod command

def update_mod(modname):
    """ update the tables with new module. """
    savepluginlist(modname)
    savecallbacktable(modname)
    savecmndtable(modname)
    