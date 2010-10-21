# gozerlib/cache.py
#
#

""" gozerlib cache provding get, set and delete functions. """

## basic imports

import logging

## defines

cache = {}

## functions

def get(name, namespace=""):
    """ get data from the cache. """
    global cache
    try: 
        data = cache[name]
        if data: logging.warn("cache - returning %s" % name) ; return data
    except KeyError: pass

def set(name, item, namespace=""):
    """ set data in the cache. """
    logging.warn("cache - setting %s (%s)" % (name, len(item)))
    global cache
    cache[name] = item

def delete(name, namespace=""):
    """ delete data from the cache. """
    try:
        global cache
        del cache[name]
        return True
    except KeyError: return False
