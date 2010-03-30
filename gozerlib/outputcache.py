# gozerlib/outputcache.py
#
#

## gozerlib imports

from persist import Persist
from utils.name import stripname

## basic imports

import os

## functions

def add(target, txtlist):

    cache = Persist('outputcache' + os.sep + stripname(target))
    d = cache.data

    if not d.has_key('msg'):
        d['msg'] = []

    d['msg'].extend(txtlist)

    while len(d['msg']) > 30:
        d['msg'].pop(0)

    cache.save()

def set(target, txtlist):
    cache = Persist('outputcache' + os.sep + stripname(target))

    if not cache.data.has_key('msg'):
        cache.data['msg'] = []

    cache.data['msg'] = txtlist
    cache.save()

def get(target):
    cache = Persist('outputcache' + os.sep + stripname(target))

    try:
        result = cache.data['msg']
        if result:
            cache.data['msg'] = []
            cache.save()
            return result

    except KeyError:
        return []

    return []
