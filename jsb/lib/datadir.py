# jsb/datadir.py
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

try: getattr(os, "mkdir") ; logging.info("datadir - shell detected") ; datadir = homedir + os.sep + ".jsb"
except AttributeError: logging.info("datadir - skipping makedirs") ; datadir = "data" ; isgae = True

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
        source = pkg_resources.resource_filename(".".join(splitted[:len(splitted)-1]), splitted[-1])
    except ImportError: 
        thedir = mod.replace(".", os.sep)
        if os.path.isdir(thedir): source = thedir
        elif os.path.isdir("/usr/lib/jsb" + os.sep + thedir): source = "/usr/lib/jsb" + os.sep + thedir
    logging.info("datadir - source is %s" % source)
    return source

def doit(ddir, mod):
    source = getsource(mod)
    if not source: raise Exception("can't find %s package" % mod)
    try:
        shutil.copytree(source, ddir + os.sep + mod.replace(".", os.sep))
    except (OSError, IOError), ex: logging.error("datadir - failed to copy %s: %s" % (mod, str(ex)))


## makedir function

def makedirs(ddir=None):
    """ make subdirs in datadir. """
    global datadir
    if os.path.exists("/var/cache/jsb") and getpass.getuser() == 'jsb': ddir = "/var/cache/jsb"
    else:
        ddir = ddir or datadir
    datadir = ddir
    logging.warn("datadir - set to %s" % datadir)
    if isgae: return
    if not os.path.isdir(ddir):
        try: os.mkdir(ddir)
        except: logging.warn("can't make %s dir" % ddir) ; os._exit(1)
        logging.info("making dirs in %s" % ddir)
    try: os.chmod(ddir, 0700)
    except: pass
    last = datadir.split(os.sep)[-1]
    if not os.path.isdir(ddir): doit(ddir, "jsb.data")
    try:
        if not os.path.isdir(ddir + os.sep + 'myplugs'): doit(ddir, "myplugs")
    except: pass
    if not os.path.isdir(ddir + os.sep + 'examples'): doit(ddir, "jsb.data.examples")
    try: touch(ddir + os.sep + "__init__.py")
    except: pass
    if not os.path.isdir(ddir + os.sep + "config"): os.mkdir(ddir + os.sep + "config")
    if not os.path.isfile(ddir + os.sep + 'config' + os.sep + "mainconfig"):
        source = getsource("jsb.data.examples")
        if not source: raise Exception("can't find jsb.data.examples package")
        try: shutil.copy(source + os.sep + 'mainconfig.example', ddir + os.sep + 'config' + os.sep + 'mainconfig')
        except (OSError, IOError), ex: logging.error("datadir - failed to copy jsb.data.config.mainconfig: %s" % str(ex))
    if not os.path.isfile(ddir + os.sep + 'config' + os.sep + "credentials.py"):
        source = getsource("jsb.data.examples")
        if not source: raise Exception("can't find jsb.data.examples package")
        try: shutil.copy(source + os.sep + 'credentials.py.example', ddir + os.sep + 'config' + os.sep + 'credentials.py')
        except (OSError, IOError), ex: logging.error("datadir - failed to copy jsb.data.config: %s" % str(ex))
    try: touch(ddir + os.sep + "config" + os.sep + "__init__.py")
    except: pass
    if not os.path.isdir(ddir + os.sep + 'myplugs'): os.mkdir(ddir + os.sep + 'myplugs')
    if not os.path.isfile(ddir + os.sep + 'myplugs' + os.sep + "__init__.py"):
        source = getsource("jsb.plugs.common")
        if not source: raise Exception("can't find jsb.plugs.common package")
        try:
            shutil.copy(source + os.sep + "__init__.py", os.path.join(ddir, 'myplugs', '__init__.py'))
        except (OSError, IOError), ex: logging.error("datadir - failed to copy myplugs/__init__.py: %s" % str(ex))
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
