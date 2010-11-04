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

curdir = os.getcwd()

if os.path.isdir("gozerdata"): datadir = "gozerdata"
else: datadir = homedir + os.sep + ".jsonbot"

## functions

def makedirs(ddir=None):
    """ make subdirs in datadir. """
    ddir = ddir or datadir
    if not os.path.isdir(ddir):
        try: os.mkdir(ddir)
        except: logging.warn("can't make %s dir" % ddir)
        logging.warn("making dirs in %s" % ddir)
    try: os.chmod(ddir, 0700)
    except: pass
    if not os.path.isdir(ddir):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', '')
            shutil.copytree(source, ddir)
        except ImportError: logging.error("datadir - failed to copy gozerdata")
    if not os.path.isdir(ddir + os.sep + 'myplugs'):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', 'myplugs')
            shutil.copytree(source, ddir + os.sep + 'myplugs')
        except ImportError: logging.error("datadir - failed to copy gozerdata/myplugs")
    if not os.path.isdir(ddir + os.sep + 'examples'):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', 'examples')
            shutil.copytree(source, ddir + os.sep + 'examples')
        except ImportError: logging.error("datadir - failed to copy gozerdata/examples")
    if not os.path.isdir(ddir + os.sep + 'config'):
        try:
            import pkg_resources
            source = pkg_resources.resource_filename('gozerdata', 'examples')
            shutil.copytree(source, ddir + os.sep + 'config')
        except ImportError: logging.error("datadir - failed to copy gozerdata/examples")
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
