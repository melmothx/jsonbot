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
    try:
        return cache[name]
    except KeyError:
        return None

def set(name, item, namespace=""):
    """ set data in the cache. """
    logging.warn("cache - setting %s (%s)" % (name, len(item)))
    cache[name] = item

def delete(name, namespace=""):
    """ delete data from the cache. """
    try:
        del cache[name]
        return True
    except KeyError:
        return False
