# gozerlib/version.py
#
#

""" version related stuff. """

version = "0.5 RC1"

## getversion function

def getversion(txt=""):
    """ return a version string. """
    if txt: return version + u" " + txt
    else: return version
