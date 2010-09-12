# gozerlib/utils/locking.py
#
#

""" generic functions """

## lib imports

from exception import handle_exception
from trace import whichmodule
from lockmanager import lockmanager, rlockmanager
from gozerlib.threads import getname

## generic imports

import logging
import sys

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
            res = None

            try:
                res = func(*args, **kwargs)
            finally:
                lock.release()
                logging.debug('locking - releasing %s' % where)
            return res

        return lockedfunc

    return locked

def locked(func):

    """ locking function for %s """ % str(func)

    def lockedfunc(*args, **kwargs):
        """ the locked function. """
        where = getname(str(func))
        try:
            logging.debug('locking - *acquire* on %s' % where)
            rlockmanager.acquire(where)
            res = None

            try:
                res = func(*args, **kwargs)
            finally:
                logging.debug('locking - *release* on %s' % where)
                rlockmanager.release(where)
        except Exception, ex:
            handle_exception()
        finally:
            rlockmanager.release(where)

        return res

    return lockedfunc
