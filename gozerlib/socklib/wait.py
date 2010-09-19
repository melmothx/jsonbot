# gozerlib/socklib/wait.py
#
#

""" wait for ircevent based on ircevent.CMND """

## gozerbot imports

from gozerlib.utils.locking import lockdec
import gozerlib.threads as thr

## basic imports

import time
import thread
import logging

## locks

waitlock = thread.allocate_lock()
locked = lockdec(waitlock)

## classes

class Wait(object):

    """ lists of ircevents to wait for """

    def __init__(self):
        self.waitlist = []
        self.ticket = 0

    def register(self, cmnd, catch, queue, timeout=15):
        """ register wait for cmnd. """
        logging.debug('irc - wait - registering for cmnd ' + cmnd)
        self.ticket += 1
        self.waitlist.insert(0, (cmnd, catch, queue, self.ticket))
        if timeout: thr.start_new_thread(self.dotimeout, (timeout, self.ticket))
        return self.ticket

    def check(self, ievent):
        """ 
            check if there are wait items for ievent .. check if 'catch' 
            matches on ievent.postfix if so put ievent on queue. 
        """
        cmnd = ievent.cmnd
        for item in self.waitlist:
            if item[0] == cmnd:
                if cmnd == "JOIN": catch = ievent.txt + ievent.postfix
                else: catch = ievent.postfix
                if item[1] in catch:
                    ievent.ticket = item[3]
                    item[2].put_nowait(ievent)
                    self.delete(ievent.ticket)
                    logging.debug('irc - wait - got response for %s' % item[0])
                    ievent.isresponse = True

    @thr.threaded
    def dotimeout(self, timeout, ticket):
        """ start timeout thread for wait with ticket nr. """
        time.sleep(float(timeout))
        self.delete(ticket)

    #@locked
    def delete(self, ticket):
        """ delete wait item with ticket nr. """
        for itemnr in range(len(self.waitlist)-1, -1, -1):
            if self.waitlist[itemnr][3] == ticket:
                self.waitlist[itemnr][2].put_nowait(None)
                del self.waitlist[itemnr]
                logging.debug('irc - deleted ' + str(ticket))
                return 1

class Privwait(Wait):

    """ wait for privmsg .. catch is on nick """

    def register(self, catch, queue, timeout=15):
        """ register wait for privmsg. """
        logging.debug('irc - privwait - registering for ' + catch)
        return Wait.register(self, 'PRIVMSG', catch, queue, timeout)

    def check(self, ievent):
        """ check if there are wait items for ievent. """
        for item in self.waitlist:
            if item[0] == 'PRIVMSG':
                if ievent.userhost == item[1]:
                    ievent.ticket = item[3]
                    item[2].put_nowait(ievent)
                    self.delete(ievent.ticket)
                    logging.debug('irc - privwait - got response for %s' % item[0])
                    ievent.isresponse = True
