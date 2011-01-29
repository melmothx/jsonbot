# jsb/boot.py
#
#

""" admin related data and functions. """

## jsb imports

from jsb.utils.generic import checkpermissions, isdebian, botuser
from jsb.lib.persist import Persist
from jsb.utils.exception import handle_exception
from jsb.lib.datadir import makedirs
from jsb.lib.config import Config
from jsb.lib.jsbimport import _import

## basic imports

import logging
import os
import sys
import types

## paths

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.getcwd() + os.sep + '..')
#try: sys.path.append(os.path.expanduser("~") + os.sep + '.jsb')
#except: pass

## defines

ongae = False
try:
    import waveapi
    plugin_packages = ['jsb.plugs.core', 'jsb.plugs.gae', 'jsb.plugs.common', 'jsb.plugs.wave', 'jsb.plugs.myplugs', 'myplugs']
    ongae = True
except ImportError: plugin_packages = ['jsb.plugs.core', 'jsb.plugs.common', 'jsb.plugs.socket', 'jsb.plugs.myplugs', 'myplugs']

default_plugins = ['jsb.plugs.core.admin', 'jsb.plugs.core.dispatch', 'jsb.plugs.core.plug']

logging.info("boot - default plugins are %s" % str(default_plugins))

loaded = False
cmndtable = None 
pluginlist = None
callbacktable = None
cmndperms = None

## boot function

def boot(ddir=None, force=False, encoding="utf-8", umask=None, saveperms=True):
    """ initialize the bot. """
    logging.info("booting ..")
    from jsb.lib.datadir import getdatadir, setdatadir
    if ddir: setdatadir(ddir)
    origdir = ddir 
    ddir = ddir or getdatadir()
    if not ddir: logging.error("can't determine datadir to boot from") ; os._exit(1)
    if not ddir in sys.path: sys.path.append(ddir)
    makedirs(ddir)
    if os.path.isdir("/var/run/jsb") and botuser() == "jsb": rundir = "/var/run/jsb"
    else: rundir = ddir + os.sep + "run"
    try:
        if os.getuid() == 0:
            print "don't run the bot as root"
            os._exit(1)
    except AttributeError: pass
    try:
        k = open(rundir + os.sep + 'jsb.pid','w')
        k.write(str(os.getpid()))
        k.close()
    except IOError: pass
    try:
        if not ongae:
            reload(sys)
            sys.setdefaultencoding(encoding)
    except (AttributeError, IOError): pass
    try:
        if not umask: checkpermissions(getdatadir(), 0700) 
        else: checkpermissions(getdatadir(), umask)  
    except: handle_exception()
    global loaded
    global cmndtable
    global pluginlist
    global callbacktable
    global cmndperms
    global plugcommands
    if not cmndtable: cmndtable = Persist(rundir + os.sep + 'cmndtable')
    if not pluginlist: pluginlist = Persist(rundir + os.sep + 'pluginlist')
    if not callbacktable: callbacktable = Persist(rundir + os.sep + 'callbacktable')
    if not cmndperms: cmndperms = Config('cmndperms', ddir=ddir)
    from jsb.lib.plugins import plugs
    if not cmndtable.data or force:
        plugs.loadall(plugin_packages, force=True)
        loaded = True
        savecmndtable(saveperms=saveperms)
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
            plugs.reload(plug, showerror=True, force=True)
        plugs.loadall(["myplugs", "jsb.plugs.myplugs"], force=True)
    logging.warn("boot - done")

## commands related commands

def savecmndtable(modname=None, saveperms=True):
    """ save command -> plugin list to db backend. """
    global cmndtable
    if not cmndtable.data: cmndtable.data = {}
    global cmndperms
    #if not cmndperms.data: cmndperms.data = {}
    from jsb.lib.commands import cmnds
    assert cmnds
    if cmnds.subs:
        for name, clist in cmnds.subs.iteritems():
            if name:
                if clist and len(clist) == 1: cmndtable.data[name] = clist[0].modname
    for cmndname, c in cmnds.iteritems():
        if modname and c.modname != modname or cmndname == "subs": continue
        if cmndname and c:
            cmndtable.data[cmndname] = c.modname  
            cmndperms[cmndname] = c.perms
    logging.info("saving command table")
    assert cmndtable
    cmndtable.save()
    if saveperms:
        logging.info("saving command perms")
        cmndperms.save()

def removecmnds(modname):
    """ remove commands belonging to modname form cmndtable. """
    global cmndtable
    assert cmndtable
    from jsb.lib.commands import cmnds
    assert cmnds
    for cmndname, c in cmnds.iteritems():
        if c.modname == modname: del cmndtable.data[cmndname]
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
    from jsb.lib.callbacks import first_callbacks, callbacks, last_callbacks, remote_callbacks
    for cb in [first_callbacks, callbacks, last_callbacks, remote_callbacks]:
        for type, cbs in cb.cbs.iteritems():
            for c in cbs:
                if modname and c.modname != modname: continue
                if not callbacktable.data.has_key(type): callbacktable.data[type] = []
                if not c.modname in callbacktable.data[type]: callbacktable.data[type].append(c.modname)
    logging.info("saving callback table")
    assert callbacktable
    callbacktable.save()

def removecallbacks(modname):
    """ remove callbacks belonging to modname form cmndtable. """
    global callbacktable
    assert callbacktable
    from jsb.lib.callbacks import first_callbacks, callbacks, last_callbacks, remote_callbacks
    for cb in [first_callbacks, callbacks, last_callbacks, remote_callbacks]:
        for type, cbs in cb.cbs.iteritems():
            for c in cbs:
                if not c.modname == modname: continue
                if not callbacktable.data.has_key(type): callbacktable.data[type] = []
                if c.modname in callbacktable.data[type]: callbacktable.data[type].remove(c.modname)
    logging.info("saving callback table")
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
    from jsb.lib.commands import cmnds
    assert cmnds
    for cmndname, c in cmnds.iteritems():
        if modname and c.modname != modname: continue
        if c and not c.plugname: logging.info("boot - not adding %s to pluginlist" % cmndname) ; continue
        if c and c.plugname not in pluginlist.data: pluginlist.data.append(c.plugname)
    pluginlist.data.sort()
    logging.info("saving plugin list")
    assert pluginlist
    pluginlist.save()

def remove_plugin(modname):
    removecmnds(modname)
    removecallbacks(modname)
    global pluginlist
    try: pluginlist.data.remove(modname.split(".")[-1]) ; pluginlist.save()
    except: pass

def clear_tables():
    global cmndtable
    global callbacktable
    global pluginlist
    cmndtable.data = {} ; cmndtable.save()
    callbacktable.data = {} ; callbacktable.save()
    pluginlist.data = [] ; pluginlist.save()

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

def whatcommands(plug):
    tbl = getcmndtable()
    result = []
    for cmnd, mod in tbl.iteritems():
        if plug in mod:
            result.append(cmnd)
    return result

def getcmndperms():
    return cmndperms

