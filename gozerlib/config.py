# gozerlib/config.py
#
#

""" config module. config is stored as item = JSON pairs. """

## gozerlib imports

from utils.trace import whichmodule
from utils.lazydict import LazyDict
from utils.exception import handle_exception
from utils.name import stripname
from datadir import datadir
from errors import CantSaveConfig

## simplejson imports

from simplejson import loads, dumps

## basic imports

import os
import types
import thread
import logging
import uuid

## classes

class Config(LazyDict):

    """ 
        config class is a dict containing json strings. is writable to file 
        and human editable.

    """

    def __init__(self, filename=None, verbose=False, input={}, *args, **kw):
        LazyDict.__init__(self, input, *args, **kw)
        self.filename = filename or 'mainconfig'
        self.dir = datadir + os.sep + 'config'
        if datadir not in self.filename: self.cfile = self.dir + os.sep + self.filename
        else: self.cfile = self.filename
        self.jsondb = None
        try:
            try: self.fromfile(self.cfile)
            except IOError:
                logging.warn("can't read config from %s" % self.cfile) 
                import waveapi
                from persist import Persist
                self.jsondb = Persist(self.cfile)
                self.update(self.jsondb.data)
                self.isdb = True
                logging.debug("config - fromdb - %s - %s" % (self.cfile, str(self)))
        except ImportError:
            handle_exception()
            self.isdb = False
        self.init()
        if not self.owner: self.owner = []
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
            self.save()

    def __getitem__(self, item):
        """ accessor function. """
        if not self.has_key(item): return None
        else: return dict.__getitem__(self, item)

    def set(self, item, value):
        """ set item to value. """
        dict.__setitem__(self, item, value)

    def fromdb(self):
        """ read config from database. """
        from gozerlib.persist import Persist
        logging.info("config - fromdb - %s" % self.cfile)
        tmp = Persist(self.cfile)
        self.update(tmp.data)

    def todb(self):
        """ save config to database. """
        cp = dict(self)
        del cp['jsondb']
        if not self.jsondb:
            from gozerlib.persist import Persist
            self.jsondb = Persist(self.cfile)
        self.jsondb.data = cp
        self.jsondb.save()

    def fromfile(self, filename):
        """ read config object from filename. """
        curline = ""
        fname = filename
        logging.debug("config - fromfile - %s" % fname)
        if not os.path.exists(fname): return
        for line in open(fname, 'r'):
            curline = line
            line = line.strip()
            if line == "" or line.startswith('#'): continue
            else:
                try:
                    key, value = line.split('=', 1)
                    self[key.strip()] = loads(unicode(value.strip()))
                except ValueError: logging.warn("config - skipping line - unable to parse: %s" % line)
        return

    def tofile(self, filename=None):
        """ save config object to file. """
        if not filename: filename = self.cfile
        try: from os import mkdir
        except ImportError:
            logging.debug("can't save %s to file .. os.mkdir() not suported" % filename)
            return
        ddir = "."
        d = []
        for p in filename.split(os.sep)[:-1]:
            d.append(p)
            ddir = os.sep.join(d)
            if not os.path.isdir(ddir):
                logging.debug("persist - creating %s dir" % ddir)
                try: os.mkdir(ddir)
                except OSError, ex:
                    logging.warn("persist - not saving - failed to make %s - %s" % (ddir, str(ex)))
                    return
        written = []
        curitem = None
        try:
            try: configlist = open(filename, 'r').readlines()
            except IOError: configlist = []
            configtmp = open(filename + '.tmp', 'w')
            teller = 0
            if not configlist: configtmp.write('# %s\n\n' % self.cfile)
            configlist.sort()
            for line in configlist:
                teller += 1
                if line.startswith('#'):
                    configtmp.write(line)
                    continue
                try:
                    keyword = line.split('=')[0].strip()
                    curitem = keyword
                except IndexError:   
                    configtmp.write(line)
                    continue
                if self.has_key(keyword):  
                    configtmp.write('%s = %s\n' % (keyword, dumps(self[keyword])))
                    written.append(keyword)
                else: configtmp.write(line)
            keywords = self.keys()
            keywords.sort()
            for keyword in keywords:
                value = self[keyword]
                if keyword in written: continue
                if keyword == 'jsondb': continue
                if keyword == 'isdb': continue
                if keyword == 'optionslist': continue
                curitem = keyword
                configtmp.write('%s = %s\n' % (keyword, dumps(value)))
            configtmp.close()
            os.rename(filename + '.tmp', self.cfile)
            return teller

        except Exception, ex:
            print "ERROR WRITING %s CONFIG FILE: %s .. %s" % (self.cfile, str(ex), curitem)

    def save(self):
        """ save the config. """
        if self.isdb: self.todb()
        else: self.tofile()
     
    def load(self, verbose=False):
        """ load the config file. """
        self.init()
        if self.isdb:self.fromdb()
        if verbose: logging.debug('PRE LOAD config %s' % str(self))

    def init(self):
        """ initialize the config object. """
        if self.filename == 'mainconfig':
            self.setdefault("whitelist", [])
            self.setdefault("blacklist", [])
            self.setdefault('owner', [])
            self.setdefault('loglist',  [])
            self.setdefault('quitmsg', "http://jsonbot.googlecode.com")
            self.setdefault('dotchars',  ", ")
            self.setdefault('floodallow', 0)
            self.setdefault('auto_register', 0)
            self.setdefault('ondemand', 1)
            self['version'] = "JSONBOT 0.5 DEVELOPMENT"
        self['createdfrom'] = whichmodule()

    def reload(self):
        """ reload the config file. """
        self.load()

def ownercheck(userhost):
    """ check whether userhost is a owner. """
    if not userhost: return False
    if userhost in cfg['owner']: return True
    return False

## global config

cfg = Config()
