# gozerlib/utils/lazydict.py
#
# thnx to maze

""" a lazydict allows dotted access to a dict .. dict.key. """

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.errors import PropertyIgnored

## simplejson imports

from simplejson import loads, dumps

## basic imports

from  xml.sax.saxutils import unescape
import copy
import logging
import uuid
import types

## defines

jsontypes = [types.StringType, types.UnicodeType, types.DictType, types.ListType, types.IntType]

defaultignore = ['cfg', 'pass', 'password', 'fsock', 'sock', 'handlers', 'users', 'plugins', 'outqueue', 'inqueue']

cpy = copy.deepcopy

## functions

def checkignore(name, ignore):
    if name.startswith('_'):
        return True
    for item in ignore:
        if item == name:
            logging.warn("lazydict - ignoring on %s" % name)
            return True
    return False

def dumpelement(element, withtypes=True):
    """ check each attribute of element whether it is dumpable. """
    new = {}
    for name in element:
        try:
            dumps(element[name])
            new[name] = element[name]
        except TypeError:
            if type(element) not in jsontypes:
                if withtypes:
                    new[name] =  unicode(type(element))
            else:
                new[name] = dumpelement(element[name], element)
    return new

## classes

class LazyDict(dict):

    """ lazy dict allows dotted access to a dict """

    def __deepcopy__(self, a):
        return LazyDict(a) 

    def __getattr__(self, attr, default=None):
        """ get attribute. """
        if not self.has_key(attr):
            self[attr] = default
            #logging.warning("setting default of %s to %s" % (attr, default))

        return self[attr]

    def __setattr__(self, attr, value):
        """ set attribute. """
        self[attr] = value

    def dostring(self):
        """ return a string representation of the dict """
        res = ""
        cp = dict(self)
        for item, value in cp.iteritems():
            res += "%r=%r " % (item, value)

        return res

    def tojson(self):
        return dumps(dumpelement(self, withtypes=False))

    def dump(self, attribs=[]):
        logging.debug("lazydict - dumping - %s" %  type(self))
        return dumps(dumpelement(self, withtypes=True))

    def load(self, input):
        """ load from json string. """  
        instr = input
        try:   
            temp = loads(instr)
        except ValueError:
            logging.error("lazydict - can't decode %s" % input)
            return self
        if type(temp) != dict:
            logging.error("lazydict - %s is not a dict" % str(temp))
            return self
        self.update(temp)
        return self
