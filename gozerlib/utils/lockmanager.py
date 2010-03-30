# gozerlib/utils/lockmanager.py
#
#

""" manages locks """

## basic imports

import thread
import threading

## classes

class LockManager(object):

    """ place to hold locks """

    def __init__(self):
        self.locks = {}

    def allocate(self, name):
        """ allocate a new lock """
        self.locks[name] = thread.allocate_lock()
        logging.debug('lockmanager - allocated %s' % name)
        
    def get(self, name):
        """ get lock """
        if not self.locks.has_key(name):
            self.allocate(name)
        return self.locks[name]
        
    def delete(self, name):
        """ delete lock """
        if self.locks.has_key(name):
            del self.locks[name]

    def acquire(self, name):
        """ acquire lock """
        if not self.locks.has_key(name):
            self.allocate(name)
        logging.debug('lockmanager - acquire %s' % name)
        self.locks[name].acquire()

    def release(self, name):
        """ release lock """
        logging.debug('lockmanager - releasing %s' % name)
        self.locks[name].release()

class RlockManager(LockManager):

    def allocate(self, name):
        """ allocate a new lock """
        self.locks[name] = threading.RLock()
        logging.debug('lockmanager - allocated RLock %s' % name)
