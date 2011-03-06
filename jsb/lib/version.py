# jsb/version.py
#
#

""" version related stuff. """

## jsb imports

from jsb.lib.datadir import getdatadir

## basic imports

import os

## defines

version = "0.7 ALPHA2"

## getversion function

def getversion(txt=""):
    """ return a version string. """
    try: tip = open(getdatadir() + os.sep + "TIP", 'r').read()
    except: tip = None
    if tip: version2 = version + " " + tip
    else: version2 = version
    if txt: return "JSONBOT %s %s" % (version2, txt)
    else: return "JSONBOT %s" % version2
