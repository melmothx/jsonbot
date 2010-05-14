# gozerlib/utils/lazydict.py
#
# thnx to maze

""" a lazydict allows dotted access to a dict .. dict.key. """

## gozerlib imports

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

defaultignore = ['plugs', 'pass', 'password']

cpy = copy.deepcopy

## functions

def dumpelement(element, ignore=[]):
    new = {}
    for name in element:
        if name in ignore:
            continue
        
        try:
            prop = getattr(element, name)
        except AttributeError:
            continue

        try:
            dumps(prop)
            new[name] = prop
            ignore.remove(name)
        except ValueError:
            continue
        except TypeError:
            try:
                new[name] = dumpelement(prop, ignore.append(name))
            except TypeError:
                new[name] = str(type(prop))
    return new

## classes

class LazyDict(dict):

    """ lazy dict allows dotted access to a dict """

    def __deepcopy__(self, a, b):
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

    def __str__(self):
        return self.dump()

    def dostring(self):
        """ return a string representation of the dict """
        res = ""
        cp = dict(self)
        for item, value in cp.iteritems():
            res += "%r=%r " % (item, value)

        return res

    def dump(self, ignore=[]):
        """ serialize this event to json. """
        return dumps(dumpelement(self, defaultignore + ignore))

    def load(self, input):
        """ load from json string. """  
        instr = unescape(input)
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
