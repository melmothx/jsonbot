# jsb/utils/lazydict.py
#
# thnx to maze

""" a lazydict allows dotted access to a dict .. dict.key. """

## jsb imports

from jsb.utils.locking import lockdec
from jsb.utils.exception import handle_exception
from jsb.lib.errors import PropertyIgnored
from jsb.imports import getjson
json = getjson()

## basic imports

from  xml.sax.saxutils import unescape
import copy
import logging
import uuid
import types
import threading
import os
import re

## locks

lock = threading.RLock()
locked = lockdec(lock)

## defines

jsontypes = [types.StringType, types.UnicodeType, types.DictType, types.ListType, types.IntType]
defaultignore = ['finished', 'inqueue', 'resqueue', 'outqueue', 'waitlist', 'comments', 'createdfrom', 'modname', 'cfile', 'dir', 'filename', 'webchannels', 'tokens', 'token', 'cmndperms', 'gatekeeper', 'stanza', 'isremote', 'iscmnd', 'orig', 'bot', 'origtxt', 'body', 'subelements', 'args', 'rest', 'cfg', 'pass', 'password', 'fsock', 'sock', 'handlers', 'users', 'plugins']
cpy = copy.deepcopy

## checkignore function

def checkignore(name, ignore):
    """ see whether a element attribute (name) should be ignored. """
    name = unicode(name)
    if name.startswith('_'): return True
    for item in ignore:
        if item == name:
            #logging.debug("lazydict - ignoring on %s" % name)
            return True
    return False

#@locked
def dumpelement(element, prev={}, withtypes=False):
    """ check each attribute of element whether it is dumpable. """
    elem = cpy(element)
    if not elem: elem = element
    try: new = dict(prev)
    except (TypeError, ValueError): new = {}
    for name in elem:
        #logging.debug("lazydict - trying dump of %s" % name) 
        if checkignore(name, defaultignore): continue
        if not elem[name]: continue
        try:
            json.dumps(elem[name])
            new[name] = elem[name]
        except TypeError:
            if type(elem) not in jsontypes:
                if withtypes: new[name] = unicode(type(elem))
            else:
                logging.warn("lazydict - dumpelement - %s" % elem[name])
                new[name] = dumpelement(elem[name], new)
    return new

## LazyDict class

class LazyDict(dict):

    """ lazy dict allows dotted access to a dict """

    def __deepcopy__(self, a):
        return LazyDict(a) 

    def __getattr__(self, attr, default=None):
        """ get attribute. """
        if not self.has_key(attr): self[attr] = default
        return self[attr]

    def __setattr__(self, attr, value):
        """ set attribute. """
        self[attr] = value

    def render(self, template):
        temp = open(template, 'r').read()
        for key, value in self.iteritems():
            try: temp = temp.replace("{{ %s }}" % key, value)
            except: pass 
        return temp

    def dostring(self):
        """ return a string representation of the dict """
        res = ""
        cp = dict(self)
        for item, value in cp.iteritems(): res += "%r=%r " % (item, value)
        return res

    def tojson(self, withtypes=False):
        """ dump the lazydict object to json. """
        try: return json.dumps(dumpelement(self, withtypes))
        except RuntimeError, ex: handle_exception()
           
    def dump(self, withtypes=False):
        """ just dunp the lazydict object. DON'T convert to json. """
        #logging.warn("lazydict - dumping - %s" %  type(self))
        try: return dumpelement(cpy(self), withtypes)
        except RuntimeError, ex: handle_exception()

    def load(self, input):
        """ load from json string. """  
        try: temp = json.loads(input)
        except ValueError:
            handle_exception()
            logging.error("lazydict - can't decode %s" % input)
            return self
        if type(temp) != dict:
            logging.error("lazydict - %s is not a dict" % str(temp))
            return self
        self.update(temp)
        return self

    def tofile(self, filename):
        f = open(filename + ".tmp", 'w')
        f.write(self.tojson())
        f.close()
        os.rename(filename + '.tmp', filename)

    def fromfile(self, filename):
        f = open(filename, "r")
        self.update(json.loads(f.read()))
