# jsb/config.py
#
#

""" config module. config is stored as item = JSON pairs. """

## jsb imports

from jsb.utils.trace import whichmodule, calledfrom
from jsb.utils.lazydict import LazyDict
from jsb.utils.exception import handle_exception
from jsb.utils.name import stripname
from datadir import getdatadir
from errors import CantSaveConfig, NoSuchFile
from jsb.utils.locking import lockdec

## simplejson imports

from jsb.imports import getjson
json = getjson()

## basic imports

import sys
import os
import types
import thread
import logging
import uuid
import thread
import getpass

## locks

savelock = thread.allocate_lock()
savelocked = lockdec(savelock)

## classes

class Config(LazyDict):

    """ 
        config class is a dict containing json strings. is writable to file 
        and human editable.

    """

    def __init__(self, filename=None, verbose=False, input={}, ddir=None, *args, **kw):
        LazyDict.__init__(self, input, *args, **kw)
        filename = filename or 'mainconfig'
        datadir = ddir or getdatadir()
        dir = datadir + os.sep + 'config'
        if datadir not in filename: cfile = dir + os.sep + filename
        else: cfile = filename
        logging.debug("config - filename is %s" % cfile)
        self.jsondb = None
        try: import waveapi ; self.isdb = True
        except ImportError: self.isdb = False
        if not self.comments: self.comments = {}
        try:
            try: self.fromfile(cfile)
            except IOError:
                logging.warn("can't read config from %s" % self.cfile) 
                import waveapi
                from persist import Persist
                self.jsondb = Persist(cfile)
                self.update(self.jsondb.data)
                self.isdb = True
                logging.debug("config - fromdb - %s - %s" % (self.cfile, str(self)))
        except ImportError:
            handle_exception()
            self.isdb = False
        self.cfile = cfile
        self.dir = dir
        self.filename = filename
        self.init()
        if not self.owner: self.owner = []
        if not self.uuid: self.uuid = str(uuid.uuid4())

    def __deepcopy__(self, a):
        """ accessor function. """
        return Config(input=self)
         
    def __getitem__(self, item):
        """ accessor function. """
        if not self.has_key(item): return None
        else: return dict.__getitem__(self, item)

    def set(self, item, value):
        """ set item to value. """
        dict.__setitem__(self, item, value)

    def fromdb(self):
        """ read config from database. """
        from jsb.lib.persist import Persist
        logging.info("config - fromdb - %s" % self.cfile)
        tmp = Persist(self.cfile)
        self.update(tmp.data)

    def todb(self):
        """ save config to database. """
        cp = dict(self)
        del cp['jsondb']
        if not self.jsondb:
            from jsb.lib.persist import Persist
            self.jsondb = Persist(self.cfile)
        self.jsondb.data = cp
        self.jsondb.save()

    @savelocked
    def fromfile(self, filename):
        """ read config object from filename. """
        curline = ""
        fname = filename
        logging.debug("config - fromfile - %s" % fname)
        if not os.path.exists(fname): return False 
        comment = ""
        for line in open(fname, 'r'):
            curline = line
            curline = curline.strip()
            if curline == "": continue
            if curline.startswith('#'): comment = curline; continue
            if True:
                try:
                    key, value = curline.split('=', 1)
                    kkey = key.strip()
                    self[kkey] = json.loads(unicode(value.strip()))
                    if comment: self.comments[kkey] = comment 
                    comment = ""
                except ValueError: logging.warn("config - skipping line - unable to parse: %s" % line)
        self.cfile = fname
        return

    @savelocked
    def tofile(self, filename=None):
        """ save config object to file. """
        if not filename: filename = self.cfile
        try: from os import mkdir
        except ImportError:
            logging.debug("can't save %s to file .. os.mkdir() not suported" % filename)
            return
        logging.debug("config - saving %s" % filename)
        if filename.startswith(os.sep): d = [os.sep,]
        else: d = []
        for p in filename.split(os.sep)[:-1]:
            if not p: continue
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
            configtmp = open(filename + '.tmp', 'w')
            teller = 0
            keywords = self.keys()
            keywords.sort()
            for keyword in keywords:
                value = self[keyword]
                if keyword in written: continue
                if keyword == 'name': continue
                if keyword == 'createdfrom': continue
                if keyword == 'cfile': continue
                if keyword == 'filename': continue
                if keyword == 'dir': continue
                if keyword == 'jsondb': continue
                if keyword == 'isdb': continue
                if keyword == 'optionslist': continue
                if keyword == 'gatekeeper': continue
                if keyword == "comments": continue
                if self.comments and self.comments.has_key(keyword):
                    configtmp.write(self.comments[keyword] + u"\n")
                curitem = keyword
                try: configtmp.write('%s = %s\n' % (keyword, json.dumps(value)))
                except TypeError: logging.error("config - %s - can't serialize %s" % (filename, keyword)) ; continue
                teller += 1
                configtmp.write("\n")
            configtmp.close()
            os.rename(filename + '.tmp', filename)
            return teller

        except Exception, ex:
            handle_exception()
            print "ERROR WRITING %s CONFIG FILE: %s .. %s" % (self.cfile, str(ex), curitem)

    def save(self):
        """ save the config. """
        logging.info("config - save called from %s" % calledfrom(sys._getframe(1)))
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
            self.comments["whitelist"] = "# whitelist used to allow ips .. bot maintains this"
            self.setdefault("whitelist", [])
            self.comments["blacklist"] = "# blacklist used to deny ips .. bot maintains this"
            self.setdefault("blacklist", [])
            self.comments["owner"] = "# global owner of all bots"
            self.setdefault('owner', [])
            self.comments["loglist"] = "# loglist .. maintained by the bot."
            self.setdefault('loglist',  [])
            self.comments["loglevel"] = "# loglevel of all bots"
            self.setdefault('loglevel',  "warn")
            self.comments["loadlist"] = "# loadlist .. not used yet."
            self.setdefault('loadlist', [])
            self.comments["quitmsg"] = "# message to send on quit"
            self.setdefault('quitmsg', "http://jsonbot.googlecode.com")
            self.comments["dotchars"] = "# characters to used as seperator"
            self.setdefault('dotchars',  ", ")
            self.comments["floodallow"] = "# whether the bot is allowed to flood."
            self.setdefault('floodallow', 0)
            self.comments["auto_register"] = "# enable automatic registration of new users"
            self.setdefault('auto_register', 0)
            self.comments["guestasuser"] = "# enable this to give new users the USER permission besides GUEST"
            self.setdefault('guestasuser', 0)
            self.comments["app_id"] = "# application id used by appengine"
            self.setdefault('app_id', "jsonbot")
            self.comments["appname"] = "# application name as used by the bot"
            self.setdefault('appnamer', "JSONBOT")
            self.comments["domain"] = "# domain .. used for WAVE"
            self.setdefault('domain', "")
        self.cfile = self.dir + os.sep + self.filename
        self['createdfrom'] = whichmodule()
        self.comments["uuid"] = "# bot generated uuid for this config file"

    def reload(self):
        """ reload the config file. """
        self.load()

def ownercheck(userhost):
    """ check whether userhost is a owner. """
    if not userhost: return False
    if userhost in cfg['owner']: return True
    return False

mainconfig = None

def getmainconfig():
    global mainconfig
    if not mainconfig: mainconfig = Config()
    return mainconfig

irctemplate = """# welcome to JSONBOT .. this file can be written to by the bot

# the name of the bot
botname = "default-irc"

# channels to join .. not implemented yet .. use /msg bot !join #channel
channels = []

# disable .. set this to 0 to enable the bot
disable = 1

# domain .. not used yet
domain = ""

# who to follow on the bot .. bot maintains this list
followlist = []

# owner of the bot .. is list of userhosts
owner = ["~dev@127.0.0.1"]

# port to connect to
port = 6667


# networkname .. not used right now
networkname = null

# whether this is a ipv6 bot
ipv6 = null

# server to connect to
server = "localhost"

# whether this is a ssl bot
ssl = null

# bot type
type = "irc"

"""

xmpptemplate = """# welcome to JSONBOT .. this file can be written to by the bot

# name of the bot
botname = "default-sxmpp"

# channels to join .. not implemented yet .. use /msg bot !join <conference>
channels = []

# disable .. set this to 0 to enable the bot
disable = 1

# domain .. not used yet
domain = ""

# who to follow on the bot .. bot maintains this list
followlist = []

# this is the host part of the user variable .. is generated by the bot
host = "localhost"

# owner of the bot .. list of JIDS
owner = ["dunk@localhost"]

# networkname .. not used right now
networkname = null

# password used 
password = "passje"

# server part of the user variable .. can be set to connect to different server then host
server = "localhost"

# type of bot .. sxmpp stands for socket xmpp to differentiate from GAE xmpp
type = "sxmpp"

# the user as which the bot should connect to the server
user = "dev@localhost"
"""

def makedefaultconfig(type, ddir=None):
    filename = 'config'
    datadir = ddir or getdatadir()
    dir = datadir + os.sep + 'config'
    ttype = "default-%s" % type
    cfile = dir + os.sep + "fleet" + os.sep + ttype + os.sep + filename
    splitted = cfile.split(os.sep)
    mdir = "" 
    for i in splitted[:-1]:
        mdir += "%s%s" % (i, os.sep)
        if not os.path.isdir(mdir): os.mkdir(mdir)
    logging.debug("config - filename is %s" % cfile)
    f = open(cfile, "w")
    if type == "irc": f.write(irctemplate) ; f.close()
    elif type == "sxmpp": f.write(xmpptemplate) ; f.close()
    else: raise Exception("no such bot type: %s" % type)
