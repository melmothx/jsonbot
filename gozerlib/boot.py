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
    plugin_packages = ['gozerlib.plugs', 'gozerlib.gae.plugs', 'commonplugs', 'gozerdata.myplugs', 'waveplugs']
    ongae = True
except ImportError:
    plugin_packages = ['gozerlib.plugs', 'gozerlib.gae.plugs', 'commonplugs', 'gozerdata.myplugs', 'waveplugs', 'socketplugs']

default_plugins = ['gozerlib.plugs.admin', 'gozerlib.plugs.dispatch', 'gozerlib.plugs.outputcache']

# these are set in gozerlib/boot.py

loaded = False
cmndtable = None 
pluginlist = None
callbacktable = None

rundir = datadir + os.sep + "run"

## functions

def boot(force=False, encoding="utf-8", umask=None):
    """ initialize the bot. """
    logging.info("booting ..")

    try:
        if os.getuid() == 0:
            print "don't run the bot as root"
            os._exit(1)
    except AttributeError:
        pass

    try:
        # write pid to pidfile  
        k = open(rundir + os.sep + 'jsonbot.pid','w')
        k.write(str(os.getpid()))
        k.close()
    except IOError:
        pass

    try:
        # set default settings
        reload(sys)
        sys.setdefaultencoding(encoding)
    except (AttributeError, IOError):
        pass

    try:
        # set umask of gozerdata dir
        if not umask:
            checkpermissions('gozerdata', 0700) 
        else:
            checkpermissions('gozerdata', umask)  
    except:
        handle_exception()

    global loaded
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
            plugs.reload(plug, force=True)

    logging.info("boot - done")

def savecmndtable():
    """ save command -> plugin list to db backend. """
    global cmndtable
    cmndtable.data = {}

    from gozerlib.commands import cmnds
    assert cmnds

    if cmnds.subs:
        for name, clist in cmnds.subs.iteritems():
            if name:
                if clist and len(clist) == 1:
                    cmndtable.data[name] = clist[0].modname   

    for cmndname, c in cmnds.iteritems():
        if cmndname and c:
            cmndtable.data[cmndname] = c.modname   

    logging.debug("saving command table")
    assert cmndtable
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
    assert callbacktable
 
    callbacktable.data = {}
  
    from gozerlib.callbacks import callbacks, remote_callbacks
    assert callbacks

    for type, cbs in callbacks.cbs.iteritems():
        for c in cbs:
            if not callbacktable.data.has_key(type):
                callbacktable.data[type] = []
            callbacktable.data[type].append(c.modname)

    for type, cbs in remote_callbacks.cbs.iteritems():
        for c in cbs:
            if not callbacktable.data.has_key(type):
                callbacktable.data[type] = []
            callbacktable.data[type].append(c.modname)

    logging.debug("saving callback table")
    assert callbacktable
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
    assert cmnds

    for cmndname, c in cmnds.iteritems():
        if c and not c.plugname:
            logging.info("boot - not adding %s to pluginlist" % cmndname)
            continue
        if c and c.plugname not in pluginlist.data:
            pluginlist.data.append(c.plugname)
    pluginlist.data.sort()
    logging.debug("saving plugin list")
    assert pluginlist
    pluginlist.save()

def getpluginlist():
    """ get the plugin list. """
    global pluginlist
    if not pluginlist:
         boot()
    return pluginlist.data
