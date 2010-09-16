# gozerlib/gatekeeper.py
#
#

## gozerlib imports

from gozerlib.persist import Persist
from gozerlib.datadir import datadir

## basic imports

import logging
import os

## classes

class GateKeeper(Persist):

    def __init__(self, name):
        self.name = name
        if not os.path.exists(datadir + os.sep +'gatekeeper'):
            os.mkdir(datadir + os.sep + 'gatekeeper')
        Persist.__init__(self, datadir + os.sep + 'gatekeeper' + os.sep + name)
        self.data.whitelist = self.data.whitelist or []

    def isblocked(self, userhost):
        if not userhost: return False
        userhost = userhost.lower()
        if userhost in self.data.whitelist:
            logging.debug("%s - allowed %s" % (self.fn, userhost))
            return False
        logging.warn("%s - denied %s" % (self.fn, userhost))
        return True

    def allow(self, userhost):
        userhost = userhost.lower()
        if not userhost in self.data.whitelist:
            self.data.whitelist.append(userhost)
            self.save()

    def deny(self, userhost):
        userhost = userhost.lower()
        if userhost in self.data.whitelist:
            self.data.whitelist.remove(userhost)
