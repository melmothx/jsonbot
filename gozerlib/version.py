# gozerlib/version.py
#
#

""" version related stuff. """

version = "0.5 RC1"

## getversion function

def getversion(txt=""):
    """ return a version string. """
    if txt: return "JSONBOT %s %s" % (version, txt)
    else: return "JSONBOT %s" % version
