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

defaultignore = ['pass', 'password', 'fsock', 'sock', 'handlers', 'users', 'plugins']
raw = ['payload', ]

cpy = copy.deepcopy

## functions

def checkignore(element, ignore):
    if unicode(element).startswith('_'):
        return True
    for item in ignore:
        if item in unicode(element):
            #logging.warn("lazydict - ignoring on %s - %s" % (item, str(element)))
            return True
    return False

def dumpelement(element, ignore=[], prev={}):
    #logging.warn("lazydict - in - %s - %s" % (str(element), str(prev)))
    from gozerlib.utils.generic import toenc
    if element == prev:
        return unicode(type(prev))
    try:
        newer = dict(prev) or {}
    except (ValueError, KeyError):
        if type(prev) in [types.StringType, types.UnicodeType, types.IntType, types.FloatType]:
            return toenc(unicode(prev))
        else:
            logging.debug("lazydict - returning prev - type %s" % type(prev))
            return unicode(type(prev))

    for name in element:
        try:
            if checkignore(name, ignore):
                newer[name] = u"jsonbot-ignored"
                continue
            if name in raw:
                logging.debug("lazydict - inserting raw element - %s" % name)
                newer[name] = toenc(getattr(element, name))
                continue
            try:
                prop = getattr(element, name)
            except AttributeError:
                logging.debug("lazydict - no %s element" % name)
                continue
            if prop == None:
                continue
            #if checkignore(prop, ignore):
            #    logging.debug("lazydict - dump - ignoring %s" % type(prop))
            #    newer[name] = unicode(type(prop))
            #    continue                

            try:
                 if type(prop) in [types.StringType, types.UnicodeType]:
                     newer[name] = toenc(unicode(prop))
                 else:
                     dumps(prop)
                     newer[name] = prop
            except (TypeError, AttributeError):
                logging.debug("lazydict - can't dump element - %s - %s" % (name, unicode(type(prop))))
                #handle_exception()
                newer[name] = unicode(type(prop))
                try:
                    if prop != element:
                        newer[name] = dumpelement(prop, ignore, prop)
                    else:
                        return str(type(prop))
                except (TypeError, AttributeError):
                    if type(prop) in [types.StringType, types.UnicodeType, types.IntType, types.FloatType, types.DictType]:
                        newer[name] =  prop
                    else:
                        newer[name] = str(type(prop))

        except TypeError:
            newer[name] = str(type(element))

    for name in newer.keys():
        if checkignore(name, ignore):
            newer[name] = "jsonbot-ignored"

    return newer

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

    def dump(self, ignore=[]):
        logging.info("lazydict - dumping - %s" %  type(self))
        result = dumpelement(self, defaultignore + ignore)
        return dumps(result)

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
