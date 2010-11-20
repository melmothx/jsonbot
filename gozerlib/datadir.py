# gozerlib/datadir.py
#
#

""" the data directory of the bot. """

## basic imports

import re
import os
import shutil
import logging
import os

## the global datadir

try: homedir = os.path.abspath(os.path.expanduser("~"))
except: homedir = os.getcwd()

isgae = False

try: getattr(os, "mkdir") ; logging.info("datadir - shell detected") ; datadir = homedir + os.sep + ".jsonbot"
except AttributeError: logging.info("datadir - skipping makedirs") ; datadir = "gozerdata" ; isgae = True

## functions

def makedirs(ddir=None):
    """ make subdirs in datadir. """
    global datadir
    ddir = ddir or datadir
    datadir = ddir
    logging.warn("datadir - %s" % datadir)
    if isgae: return
    if not os.path.isdir(ddir):
        try: os.mkdir(ddir)
        except: logging.warn("can't make %s dir" % ddir)
        logging.warn("making dirs in %s" % ddir)
    try: os.chmod(ddir, 0700)
    except: pass
    last = datadir.split(os.sep)[-1]
    if not os.path.isdir(ddir):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', '')
            shutil.copytree(source, ddir)
        except ImportError: 
            try:
                source = "/usr/local/gozerdata"
                shutil.copytree(source, ddir)
            except: logging.error("datadir - failed to copy gozerdata")
    if not os.path.isdir(ddir + os.sep + 'myplugs'):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', 'myplugs')
            shutil.copytree(source, ddir + os.sep + 'myplugs')
        except ImportError: 
            try:
                source = "/usr/local/gozerdata/myplugs"
                shutil.copytree(source, ddir + os.sep + "myplugs")
            except: logging.error("datadir - failed to copy gozerdata/myplugs")
    if not os.path.isdir(ddir + os.sep + 'examples'):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', 'examples')
            shutil.copytree(source, ddir + os.sep + 'examples')
        except ImportError: 
            try:
                source = "/usr/local/gozerdata/examples"
                shutil.copytree(source, ddir + os.sep + "examples")
            except: logging.error("datadir - failed to copy gozerdata/examples")
    if not os.path.isdir(ddir + os.sep + 'config'):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', 'examples')
            shutil.copytree(source, ddir + os.sep + 'config')
        except ImportError: 
            try:
                source = "/usr/local/gozerdata/examples"
                shutil.copytree(source, ddir + os.sep + "config")
            except: logging.error("datadir - failed to copy gozerdata/myplugs")
    try:
        import pkg_resources
        source = pkg_resources.resource_filename('commonplugs', '')
        shutil.copyfile(source + os.sep + "__init__.py", ddir + os.sep + '__init__.py')
    except ImportError: pass
    if not os.path.isdir(ddir + os.sep + 'myplugs'): os.mkdir(ddir + os.sep + 'myplugs')
    try:
        import pkg_resources
        source = pkg_resources.resource_filename('commonplugs', '')
        shutil.copyfile(source + os.sep + "__init__.py", os.path.join(ddir,'myplugs', '__init__.py'))
    except ImportError: pass
    if not os.path.isdir('/var/log/jsonbot') and not os.path.isdir(os.getcwd() + os.sep + 'jsonbot.logs'): 
        os.mkdir(os.getcwd() + os.sep + 'jsonbot.logs')
    if not os.path.isdir(ddir + '/run/'): os.mkdir(ddir + '/run/')
    if not os.path.isdir(ddir + '/run/'): os.mkdir(ddir + '/run/')
    if not os.path.isdir(ddir + '/examples/'): os.mkdir(ddir + '/examples/')
    if not os.path.isdir(ddir + '/config/'): os.mkdir(ddir + '/config/')
    if not os.path.isdir(ddir + '/users/'): os.mkdir(ddir + '/users/')
    if not os.path.isdir(ddir + '/channels/'): os.mkdir(ddir + '/channels/')
    if not os.path.isdir(ddir + '/fleet/'): os.mkdir(ddir + '/fleet/')
    if not os.path.isdir(ddir + '/pgp/'): os.mkdir(ddir + '/pgp/')
    if not os.path.isdir(ddir + '/plugs/'): os.mkdir(ddir + '/plugs/')
    if not os.path.isdir(ddir + '/old/'): os.mkdir(ddir + '/old/')

def getdatadir():
    global datadir
    return datadir