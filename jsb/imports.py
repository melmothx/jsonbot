# jsb/imports.py
#
#

""" provide a import wrappers for the contrib packages. """

## lib imports

from lib.jsbimport import _import

## basic imports

import logging

## getjson function

def getjson():
    try: mod = _import("json")
    except:
        try:
            mod = _import("simplejson")
        except:
            mod = _import("contrib.simplejson")
    logging.debug("imports - module is %s" % str(mod))
    return mod

## getfeedparser function

def getfeedparser():
    try: mod = _import("feedparser")
    except:
        mod = _import("contrib.feedparser")
    logging.debug("imports - module is %s" % str(mod))
    return mod

def getoauth():
    try: mod = _import("oauth")
    except:
        mod = _import("contrib.oauth")
    logging.debug("imports - module is %s" % str(mod))
    return mod
