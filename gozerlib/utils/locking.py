# gozerlib/utils/locking.py
#
#

""" locking functions """

## gozerlib imports

from exception import handle_exception
from trace import whichmodule
from lockmanager import lockmanager, rlockmanager
from gozerlib.threads import getname

## generic imports

import logging
import sys

## Locked class

class Locked(object):

    """ class used to lock an entire object. UNTESTED"""

    def __getattribute__(self, attr):
        where = whichmodule(1)
        logging.debug('locking - locking on %s' % where)
        rlockmanager.acquire(object)
        res = None
        try: res = super(Locked, self).__getattribute__(attr)
        finally: rlockmanager.release(object)
        return res

## lockdec function

def lockdec(lock):
    """ locking decorator. """
    def locked(func):
        """ locking function for %s """ % str(func)
        def lockedfunc(*args, **kwargs):
            """ the locked function. """
            where = whichmodule(2)
            logging.debug('locking - locking on %s' % where)
            lock.acquire()
            res = None
            try: res = func(*args, **kwargs)
            finally:
                lock.release()
                logging.debug('locking - releasing %s' % where)
            return res
        return lockedfunc
    return locked

## locked decorator

def locked(func):
    """ function locking decorator """
    def lockedfunc(*args, **kwargs):
        """ the locked function. """
        where = getname(str(func))
        try:
            rlockmanager.acquire(where)
            res = func(*args, **kwargs)
        finally: rlockmanager.release(where)
        return res
    return lockedfunc
