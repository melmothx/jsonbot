# gozerlib/utils/lazydict.py
#
# thnx to maze

""" a lazydict allows dotted access to a dict .. dict.key. """

## simplejson imports

from simplejson import loads, dumps

## basic imports
from  xml.sax.saxutils import unescape
import copy
import logging

## defines

cpy = copy.deepcopy

## classes

class LazyDict(dict):

    """ lazy dict allows dotted access to a dict """


    def __getattr__(self, attr, default=None):
        """ get attribute. """
        if not self.has_key(attr):
            self[attr] = default

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

    def dump(self):
        """ serialize this event to json. """
        new = {}
        for name in self:
            try:
                prop = getattr(self, name)
                dumps(prop)
                new[name] = prop
            except TypeError:
                pass
        logging.debug('lazydict - tojson - %s' % str(new))
        return dumps(new)

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
