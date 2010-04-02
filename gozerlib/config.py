# gozerlib/config.py
#
#

""" config module. """

## gozerlib imports

from utils.trace import whichmodule
from utils.lazydict import LazyDict
from utils.exception import handle_exception
from datadir import datadir
from errors import CantSaveConfig

## simplejson imports

from simplejson import loads, dumps

## basic imports

import os
import types
import thread
import logging

## classes

class Config(LazyDict):

    """ 
        config class is a dict containing json strings. is writable to file 
        and human editable.

        :param filename: filename of the config file
        :type filename: string
        :param verbose: whether loading of config should ne verbose
        :type verbose: boolean
        :rtype: self
    """

    def __init__(self, filename=None, verbose=False, *args, **kw):
        LazyDict.__init__(self, *args, **kw)
        #self.dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__ + os.sep + '..')))
        self.filename = filename or 'mainconfig'
        self.dir = 'config'
        self.cfile = self.dir + os.sep + self.filename
        self.init()
        self.jsondb = None

        try:
            self.fromfile(self.cfile)
            self.isdb = False
        except IOError:
            from persist import Persist
            self.jsondb = Persist(self.cfile)
            self.update(self.jsondb.data)
            self.isdb = True
            logging.debug("config - fromdb - %s - %s" % (self.cfile, str(self)))


    def __getitem__(self, item):
        if not self.has_key(item):
            return None
        else:
            return dict.__getitem__(self, item)

    def set(self, item, value):

        """
            set item to value.

            :param item: item to set value of
            :type item: string
            :param value: value to set
            :type value: dict, list, string, number or boolean

        """

        dict.__setitem__(self, item, value)
        return self

    def fromdb(self):

        """ read config from database. """
        from gozerlib.persist import Persist
        logging.info("config - fromdb - %s" % self.cfile)

        tmp = Persist(self.cfile)
        self.update(tmp.data)
        return self

    def todb(self):

        """ save config to database. """

        
        cp = dict(self)
        del cp['jsondb']
        if not self.jsondb:
            from gozerlib.persist import Persist
            self.jsondb = Persist(self.cfile)
        self.jsondb.data = cp
        self.jsondb.save()
        return self

    def fromfile(self, filename):

        """ 
            read config object from filename. 

            :param filename: name of file to write to
            :type filename: string
            :rtype: self

        """

        curline = ""

        # read file and set config values to loaded JSON entries
        fname = filename
        logging.info("config - fromfile - %s" % fname)
 
        if not os.path.exists(fname):
            return self
 
        # open file

        f = open(fname, 'r')

        # loop over data in config file            
        for line in f:
            curline = line
            line = line.strip()

            if not line or line.startswith('#'):
                continue
            else:
                key, value = line.split('=', 1)
                self[key.strip()] = loads(unicode(value.strip()))

        return self

    def tofile(self, filename=None):

        """ save config object to file. """

        if not filename:
            filename = self.cfile

        try:
            from os import mkdir
        except ImportError:
            logging.debug("can't save %s to file .. os.mkdir() not suported" % filename)
            return

        ddir = "."
        d = []

        for p in filename.split(os.sep)[:-1]:
            d.append(p)
            ddir = os.sep.join(d)
            if not os.path.isdir(ddir):
                logging.warn("persist - creating %s dir" % ddir)
                os.mkdir(ddir)

        #logging.warn("config - tofile - %s" % ddir)
        written = []
        curitem = None

        try:
            # read existing config file if available
            try:
                configlist = open(filename, 'r').readlines()
            except IOError:
                configlist = []

            # make temp file
            configtmp = open(filename + '.tmp', 'w')
            teller = 0

            # write header if not already there
            if not configlist:
                configtmp.write('# %s\n\n' % self.cfile)

            # loop over original lines replacing updated data
            for line in configlist:
                teller += 1

                # skip comment
                if line.startswith('#'):
                    configtmp.write(line)
                    continue

                # take part after the =
                try:
                    keyword = line.split('=')[0].strip()
                    curitem = keyword
                except IndexError:   
                    configtmp.write(line)
                    continue

                # write JSON string of data
                if self.has_key(keyword):  
                    configtmp.write('%s = %s\n' % (keyword, dumps(self[keyword])))
                    written.append(keyword)
                else:
                    configtmp.write(line)

            # write data not found in original config file
            for keyword, value in self.iteritems():
                if keyword in written:
                    continue
                if keyword == 'jsondb':
                    continue
                if keyword == 'isdb':
                    continue
                if keyword == 'optionslist':
                    continue
                curitem = keyword
                configtmp.write('%s = %s\n' % (keyword, dumps(value)))

            # move temp file to original
            configtmp.close()

            try:
                os.rename(filename + '.tmp', self.cfile)
            except WindowsError:
                # no atomic operation supported on windows! error is thrown when destination exists
                os.remove(filename)
                os.rename(filename + '.tmp', self.cfile)

            return teller

        except Exception, ex:
            print "ERROR WRITING %s CONFIG FILE: %s .. %s" % (self.cfile, str(ex), curitem)

        return self

    def save(self):
        if self.isdb:
            self.todb()
        else:
            self.tofile()
     
    def load(self, verbose=False):

        """
            load the config file.

            :param verbose: whether loading should be verbose
        """

        self.init()

        if self.isdb:
            self.fromdb()

        if verbose:
            logging.debug('PRE LOAD config %s' % str(self))

        return self

    def init(self):

        if self.filename == 'mainconfig':
            self.setdefault('owner', [])
            self.setdefault('loglist',  [])
            self.setdefault('quitmsg', "http://jsonbot.googelcode.com")
            self.setdefault('debug', 0)
            self.setdefault('plugdeny', [])
            self.setdefault('dotchars',  " .. ")
            self.setdefault('floodallow', 1)
            self.setdefault('auto_register', 1)
            self.setdefault('ondemand', 1)

        self['version'] = "JSONBOT 0.1.1"

        return self

    def reload(self):

        """
            reload the config file.

        """

        self.load()
        return self

def ownercheck(userhost):

    """
        check whether userhost is a owner.
 
        :param userhost: userhost to check
        :type userhost: string
        :rtype: boolean

    """

    if not userhost:
        return False

    if userhost in cfg['owner']:
        return True

    return False

## define

cfg = Config()
