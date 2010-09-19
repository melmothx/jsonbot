# gozerlib/outputcache.py
#
#

## gozerlib imports

from persist import Persist
from utils.name import stripname
from datadir import datadir

## basic imports

import os
import logging

## clear function

def clear(target):
    """ clear target's outputcache. """
    cache = Persist(datadir + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    try:
        result = cache.data['msg']
        if result:
            cache.data['msg'] = []
            cache.save()
            return result
    except KeyError: pass
    return []

## add function

def add(target, txtlist):
    """ add list of txt to target entry. """
    logging.warn("outputcache - adding %s lines" % len(txtlist))
    cache = Persist(datadir + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    d = cache.data
    if not d.has_key('msg'): d['msg'] = []
    d['msg'].extend(txtlist)
    while len(d['msg']) > 10: d['msg'].pop(0)
    cache.save()

## set function

def set(target, txtlist):
    """ set target entry to list. """
    cache = Persist(datadir + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    if not cache.data.has_key('msg'): cache.data['msg'] = []
    cache.data['msg'] = txtlist
    cache.save()

## get function

def get(target):
    """ get output for target. """
    cache = Persist(datadir + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    try:
        result = cache.data['msg']
        if result: return result
    except KeyError: pass
    return []
