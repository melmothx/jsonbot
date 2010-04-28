# gozerlib/jsbimport.py
#
#

""" use the imp module to import modules. """

## basic imports

import time
import sys
import imp
import os
import thread
import logging

## functions

def _import(name):
    """ do a import (full). """
    mods = []
    mm = ""
    for m in name.split('.'):
        mm += m
        mods.append(mm)
        mm += "."

    for mod in mods:
        logging.debug("jsbimport - trying %s" % mod)
        imp = __import__(mod)

    logging.debug("jsbimport - got module %s" % sys.modules[name])
    return sys.modules[name]

def force_import(name):
    """ force import of module <name> by replacing it in sys.modules. """
    try:
        del sys.modules[name]
    except KeyError:
        pass
    plug = _import(name)
    return plug
