# gozerlib/datadir.py
#
#

""" the data directory of the bot. """

## basic imports

import re
import os

## define

datadir = 'gozerdata'

## functions

def makedirs(ddir=None):
    """ make subdirs in datadir. users, db, fleet, pgp, plugs and old. """
    ddir = ddir or datadir
    curdir = os.getcwd()

    if not os.path.isdir(ddir):
        os.mkdir(ddir)
    if not os.path.isdir(ddir + '/users/'):
        os.mkdir(ddir + '/users/')
    if not os.path.isdir(ddir + '/db/'):
        os.mkdir(ddir + '/db/')
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
