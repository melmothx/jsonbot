# gozerlib/gatekeeper.py
#
#

## gozerlib imports

from gozerlib.persist import Persist
from gozerlib.datadir import datadir

## basic imports

import logging

## classes

class GateKeeper(Persist):

    def __init__(self, filename):
        Persist.__init__(self, filename)
        self.data.whitelist = self.data.whitelist or []

    def isblocked(self, userhost):
        userhost = userhost.lower()
        if userhost in self.data.whitelist:
            logging.warn("%s - allowed %s" % (self.fn, userhost))
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
