# gozerlib/datadir.py
#
#

""" the data directory of the bot. """

## basic imports

import re
import os
import shutil
import logging
import os.path
import getpass

## the global datadir

try: homedir = os.path.abspath(os.path.expanduser("~"))
except: homedir = os.getcwd()

isgae = False

try: getattr(os, "mkdir") ; logging.info("datadir - shell detected") ; datadir = homedir + os.sep + ".jsonbot"
except AttributeError: logging.info("datadir - skipping makedirs") ; datadir = "gozerdata" ; isgae = True

## helper functions

def touch(fname):
    """ touch a file. """
    fd = os.open(fname, os.O_WRONLY | os.O_CREAT)
    os.close(fd)

def getsource(mod):
    source = None
    splitted = mod.split(".")
    if len(splitted) == 1: splitted.append("")
    try:
        import pkg_resources
        source = pkg_resources.resource_filename(*splitted)
    except ImportError: 
        thedir = mod.replace(".", os.sep)
        if os.path.isdir(thedir): source = thedir
        elif os.path.isdir("/var/lib/jsonbot" + os.sep + thedir): source = "/var/lib/jsonbot" + os.sep + thedir
    return source

## makedir function

def makedirs(ddir=None):
    """ make subdirs in datadir. """
    global datadir
    if os.path.exists("/etc/debian_version") and getpass.getuser() == 'jsonbot': ddir = "/var/cache/jsonbot"
    else:
        ddir = ddir or datadir
    datadir = ddir
    logging.warn("datadir - %s" % datadir)
    if isgae: return
    if not os.path.isdir(ddir):
        try: os.mkdir(ddir)
        except: logging.warn("can't make %s dir" % ddir) ; os._exit(1)
    logging.warn("making dirs in %s" % ddir)
    try: os.chmod(ddir, 0700)
    except: pass
    last = datadir.split(os.sep)[-1]
    if not os.path.isdir(ddir):
        source = getsource("gozerdata")
        if not source: raise Exception("can't find gozerdata package")
        try:
            shutil.copytree(source, ddir)
        except (OSError, IOError), ex: logging.error("datadir - failed to copy gozerdata: %s" % str(ex))
    if not os.path.isdir(ddir + os.sep + 'myplugs'):
        source = getsource("gozerdata.myplugs")
        if not source: raise Exception("can't find gozerdata.myplugs package")
        try:
            shutil.copytree(source, ddir + os.sep + "myplugs")
        except (OSError, IOError), ex: logging.error("datadir - failed to copy gozerdata.myplugs: %s" % str(ex))
    if not os.path.isdir(ddir + os.sep + 'examples'):
        source = getsource("gozerdata.examples")
        if not source: raise Exception("can't find gozerdata.examples package")
        try:
            shutil.copytree(source, ddir + os.sep + "examples")
        except (OSError, IOError), ex: logging.error("datadir - failed to copy gozerdata.examples: %s" % str(ex))
    if not os.path.isdir(ddir + os.sep + 'config'):
        source = getsource("gozerdata.config")
        if not source: raise Exception("can't find gozerdata.config package")
        try:
            shutil.copytree(source, ddir + os.sep + "config")
        except (OSError, IOError), ex: logging.error("datadir - failed to copy gozerdata.config: %s" % str(ex))
    try: touch(ddir + os.sep + "__init__.py")
    except: pass
    try: touch(ddir + os.sep + "config" + os.sep + "__init__.py")
    except: pass
    if not os.path.isdir(ddir + os.sep + 'myplugs'): os.mkdir(ddir + os.sep + 'myplugs')
    if not os.path.isfile(ddir + os.sep + 'myplugs' + os.sep + "__init__.py"):
        source = getsource("commonplugs")
        if not source: raise Exception("can't find commonplugs package")
        try:
            shutil.copy(source + os.sep + "__init__.py", os.path.join(ddir, 'myplugs', '__init__.py'))
        except (OSError, IOError), ex: logging.error("datadir - failed to copy gozerdata.config: %s" % str(ex))
    if not os.path.isdir(ddir + os.sep +'botlogs'): os.mkdir(ddir + os.sep + 'botlogs')
    if not os.path.isdir(ddir + '/run/'): os.mkdir(ddir + '/run/')
    if not os.path.isdir(ddir + '/examples/'): os.mkdir(ddir + '/examples/')
    if not os.path.isdir(ddir + '/users/'): os.mkdir(ddir + '/users/')
    if not os.path.isdir(ddir + '/channels/'): os.mkdir(ddir + '/channels/')
    if not os.path.isdir(ddir + '/fleet/'): os.mkdir(ddir + '/fleet/')
    if not os.path.isdir(ddir + '/pgp/'): os.mkdir(ddir + '/pgp/')
    if not os.path.isdir(ddir + '/plugs/'): os.mkdir(ddir + '/plugs/')
    if not os.path.isdir(ddir + '/old/'): os.mkdir(ddir + '/old/')

def getdatadir():
    global datadir
    return datadir
