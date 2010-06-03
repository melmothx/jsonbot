# gozerlib/datadir.py
#
#

""" the data directory of the bot. """

## basic imports

import pkg_resources
import re
import os
import shutil
import logging

## define

datadir = 'jsondir'

## functions

def makedirs(ddir=None):
    """ make subdirs in datadir. """
    ddir = ddir or datadir
    curdir = os.getcwd()
    logging.warn("make dirs in %s" % ddir)

    if not os.path.isdir(ddir):
        os.mkdir(ddir)
    source = pkg_resources.resource_filename('commonplugs', '')
    shutil.copyfile(source + os.sep + "__init__.py", ddir + os.sep + '__init__.py')
    if not os.path.isdir(ddir + os.sep + 'myplugs'):
        os.mkdir(ddir + os.sep + 'myplugs')
    source = pkg_resources.resource_filename('commonplugs', '')
    shutil.copyfile(source + os.sep + "__init__.py", os.path.join(ddir,'myplugs', '__init__.py'))
    if not os.path.isdir(ddir + '/config/'):
        os.mkdir(ddir + '/config/')
    if not os.path.isdir(ddir + '/users/'):
        os.mkdir(ddir + '/users/')
    if not os.path.isdir(ddir + '/channels/'):
        os.mkdir(ddir + '/channels/')
    if not os.path.isdir(ddir + '/fleet/'):
        os.mkdir(ddir + '/fleet/')
    if not os.path.isdir(ddir + '/pgp/'):
        os.mkdir(ddir + '/pgp/')
    if not os.path.isdir(ddir + '/plugs/'):
        os.mkdir(ddir + '/plugs/')
    if not os.path.isdir(ddir + '/old/'):
        os.mkdir(ddir + '/old/')
        return True
