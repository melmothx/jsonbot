# gozerlib/outputcache.py
#
#

## gozerlib imports

from persist import Persist
from utils.name import stripname
from datadir import getdatadir
from gozerlib.utils.timeutils import hourmin

## basic imports

import os
import logging
import time

## clear function

def clear(target):
    """ clear target's outputcache. """
    cache = Persist(getdatadir() + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    try:
        cache.data['msg'] = []
        cache.save()
    except KeyError: pass
    return []

## add function

def add(target, txtlist):
    """ add list of txt to target entry. """
    logging.warn("outputcache - adding %s lines" % len(txtlist))
    t = []
    for item in txtlist:
        t.append("[%s] %s" % (hourmin(time.time()), item))
    cache = Persist(getdatadir() + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    d = cache.data
    if not d.has_key('msg'): d['msg'] = []
    d['msg'].extend(t)
    while len(d['msg']) > 10: d['msg'].pop(0)
    cache.save()

## set function

def set(target, txtlist):
    """ set target entry to list. """
    t = []
    for item in txtlist:
        t.append("[%s] %s" % (hourmin(time.time()), item))
    cache = Persist(getdatadir() + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    if not cache.data.has_key('msg'): cache.data['msg'] = []
    cache.data['msg'] = t
    cache.save()

## get function

def get(target):
    """ get output for target. """
    cache = Persist(getdatadir() + os.sep + 'run' + os.sep + 'outputcache' + os.sep + stripname(target))
    try:
        result = cache.data['msg']
        if result: return result
    except KeyError: pass
    return []
