# gozerlib/version.py
#
#

""" version related stuff. """

## gozerlib imports

from gozerlib.datadir import getdatadir

## basic imports

import os

## defines

version = "0.5 RC1"

## getversion function

def getversion(txt=""):
    """ return a version string. """
    try: tip = open(getdatadir() + os.sep + "TIP", 'r').read()
    except: tip = None
    global version
    if tip: version += " " + tip
    if txt: return "JSONBOT %s %s" % (version, txt)
    else: return "JSONBOT %s" % version
