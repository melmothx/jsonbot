# gozerlib/persist.py
#
#

"""
    allow data to be written to disk or BigTable in JSON format. creating 
    the persisted object restores data. 

"""

## gozerlib imports

from utils.trace import whichmodule, calledfrom
from utils.lazydict import LazyDict
from utils.exception import handle_exception
from utils.name import stripname
from utils.locking import lockdec
from datadir import datadir

## simplejson imports

from simplejson import load, dump, loads, dumps

## basic imports

import thread
import logging
import os
import types
import copy
import sys

## try google first

try:
    from google.appengine.ext import db
    from google.appengine.api.memcache import get, set
    from google.appengine.api.datastore_errors import Timeout
    logging.debug("persist - using BigTable based Persist")

    ## JSONindb class

    class JSONindb(db.Model):
        """ model to store json files in. """
        modtime = db.DateTimeProperty(auto_now=True, indexed=False)
        createtime = db.DateTimeProperty(auto_now_add=True, indexed=False)
        filename = db.StringProperty()
        content = db.TextProperty(indexed=False)

    ## Persist class

    class Persist(object):

        """ persist data attribute to database backed JSON file. """ 

        def __init__(self, filename, default={}):
            self.plugname = calledfrom(sys._getframe())
            if 'lib' in self.plugname: self.plugname = calledfrom(sys._getframe(1))
            self.fn = unicode(filename.strip()) # filename to save to
            self.logname = os.sep.join(self.fn.split(os.sep)[-2:])
            self.key = None
            self.obj = None
            jsontxt = get(self.fn)
            if type(default) == types.DictType:
                default2 = LazyDict()
                default2.update(default)
            else: default2 = copy.deepcopy(default)
            if jsontxt is None:
                logging.debug("persist - %s - loading from db" % self.logname) 
                try:
                    try: self.obj = JSONindb.get_by_key_name(self.fn)
                    except Timeout: self.obj = JSONindb.get_by_key_name(self.fn)
                except Exception, ex:
                    handle_exception()
                    self.data = default2
                    return
                if self.obj == None:
                    logging.debug("persist - %s - no entry found" % self.logname)
                    self.obj = JSONindb(key_name=self.fn)
                    self.obj.content = unicode(default)
                    self.data = default2
                    return
                jsontxt = self.obj.content
                if jsontxt: set(self.fn, jsontxt)
                logging.debug('persist - jsontxt is %s' % jsontxt)
                gotcache = False
            else: gotcache = True
            self.data = loads(jsontxt)
            if type(self.data) == types.DictType:
                d = LazyDict()
                d.update(self.data)
                self.data = d
            cfrom = whichmodule()
            if 'gozerlib' in cfrom: 
                cfrom = whichmodule(2)
                if 'gozerlib' in cfrom: cfrom = whichmodule(3)
            cfrom = whichmodule(2)
            if 'gozerlib' in cfrom: 
                cfrom = whichmodule(3)
                if 'gozerlib' in cfrom: cfrom = whichmodule(4)
            if not 'run' in self.fn: 
                if gotcache: logging.info("persist - cache - loaded %s (%s) - %s - %s" % (self.logname, len(jsontxt), self.data.tojson(), cfrom))
                else: logging.info("persist - db - loaded %s (%s) - %s - %s" % (self.logname, len(jsontxt), self.data.tojson(), cfrom))
     
        def save(self):
            """ save json data to database. """
            bla = dumps(self.data)
            if self.obj == None:
                self.obj = JSONindb(key_name=self.fn)
                self.obj.content = bla
            else: self.obj.content = bla
            self.obj.filename = self.fn
            key = self.obj.put()  
            cfrom = whichmodule(0)
            if 'gozerlib' in cfrom: 
                cfrom = whichmodule(2)
                if 'gozerlib' in cfrom: cfrom = whichmodule(3)
            logging.warn('persist - %s - saved %s (%s)' % (cfrom, self.logname, len(bla)))
            set(self.fn, bla)

except ImportError:

    ## file based persist

    logging.debug("using file based Persist")

    ## defines

    persistlock = thread.allocate_lock()
    persistlocked = lockdec(persistlock)
    from gozerlib.cache import get, set

    ## classes

    class Persist(object):

        """ persist data attribute to JSON file. """

        def __init__(self, filename, default=None, init=True):
            """ Persist constructor """
            self.fn = filename.strip() # filename to save to
            self.logname = os.sep.join(self.fn.split(os.sep)[-2:])
            self.lock = thread.allocate_lock() # lock used when saving)
            self.data = LazyDict() # attribute to hold the data
            if init:
                if default == None: default = LazyDict()
                self.init(default)

        @persistlocked
        def init(self, default={}):
            """ initialize the data. """
            logging.debug('persist - reading %s' % self.fn)
            gotcache = False
            try:
                data = get(self.fn)
                if not data:
                   datafile = open(self.fn, 'r')
                   data = datafile.read()
                   datafile.close()
                   set(self.fn, data)
                else: gotcache = True
            except IOError, ex:
                if not 'No such file' in str(ex):
                    logging.error('persist - failed to read %s: %s' % (self.logname, str(ex)))
                    raise
                else:
                    logging.debug("persist - %s doesn't exist yet" % self.logname)
                    return

            try:
                self.data = loads(data)
                if type(self.data) == types.DictType:
                    d = LazyDict()
                    d.update(self.data)
                    self.data = d
                cfrom = whichmodule(2)
                if 'gozerlib' in cfrom: 
                    cfrom = whichmodule(3)
                    if 'gozerlib' in cfrom: cfrom = whichmodule(4)
                if not 'run' in self.fn: 
                    size = len(data)
                    if gotcache: logging.info("persist - cache - loaded %s (%s) - %s - %s" % (self.logname, size, self.data.tojson(), cfrom))
                    else: logging.info("persist - file - loaded %s (%s) - %s - %s" % (self.logname, size, self.data.tojson(), cfrom))
            except Exception, ex:
                logging.error('persist - ERROR: %s' % self.fn)
                raise

        def get(self):
           return loads(get(self.fn)) 

        @persistlocked
        def sync(self):
           logging.warn("persist - syncing %s" % self.fn)
           data = dumps(self.data)
           set(self.fn, data)
           return data

        @persistlocked
        def save(self):
            """ persist data attribute. """
            try:
                data = dumps(self.data)
                set(self.fn, data)
                dirr = []
                for p in self.fn.split(os.sep)[:-1]:
                    dirr.append(p)
                    pp = os.sep.join(dirr)
                    if not os.path.isdir(pp):
                        logging.warn("persist - creating %s dir" % pp)
                        os.mkdir(pp)
                tmp = self.fn + '.tmp' # tmp file to save to
                try: datafile = open(tmp, 'w')
                except IOError, ex:
                    logging.error("persist - can't save %s: %s" % (self.logname, str(ex)))
                    return
                dump(self.data, datafile)
                datafile.close()
                try: os.rename(tmp, self.fn)
                except OSError:
                    #handle_exception()
                    os.remove(self.fn)
                    os.rename(tmp, self.fn)
                set(self.fn, data)
                logging.warn('persist - %s saved (%s)' % (self.logname, len(data)))
            finally: pass

class PlugPersist(Persist):

    """ persist plug related data. data is stored in jsondata/plugs/{plugname}/{filename}. """

    def __init__(self, filename, default=None):
        plugname = calledfrom(sys._getframe())
        Persist.__init__(self, datadir + os.sep + 'plugs' + os.sep + stripname(plugname) + os.sep + stripname(filename))
