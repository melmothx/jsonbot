# gozerlib/utils/locking.py
#
#

""" generic functions """

## lib imports

from trace import whichmodule
from lockmanager import LockManager, RLockManager

## generic imports

import logging
import sys

## defines

locks = []
lockmanager = LockManager()
rlockmanager = RLockManager()

## classes

class Locked(object):

    """ class used to lock an entire object. UNTESTED"""

    def __getattribute__(self, attr):
        where = whichmodule(1)
        logging.debug('locking - locking on %s' % where)
        rlockmanager.acquire(object)
        res = None

        try:
            res = super(Locked, self).__getattribute__(attr)
        finally:
            rlockmanager.release(object)

        return res

## functions

def lockdec(lock):

    """ locking decorator. """

    def locked(func):

        """ locking function for %s """ % str(func)

        def lockedfunc(*args, **kwargs):
            """ the locked function. """
            where = whichmodule(1)
            logging.debug('locking - locking on %s' % where)
            lock.acquire()
            locks.append(str(func))
            res = None

            try:
                res = func(*args, **kwargs)
            finally:
                lock.release()
                locks.remove(str(func))
                logging.debug('locking - releasing %s' % where)
            return res

        return lockedfunc

    return locked

def funclocked(func):

    """ locking function for %s """ % str(func)

    def lockedfunc(*args, **kwargs):
        """ the locked function. """
        where = whichmodule(1)
        logging.debug('locking - locking on %s' % where)
        rlockmanager.acquire(func)
        locks.append(str(func))
        res = None

        try:
            res = func(*args, **kwargs)
        finally:
            rlockmanager.release(func)
            locks.remove(str(func))

        return res

    return lockedfunc
