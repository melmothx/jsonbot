# gozerlib/fleet.py
#
#

""" fleet is a list of bots. """

## gozerlib imports

from utils.exception import handle_exception
from utils.generic import waitforqueue
from config import Config
from config import cfg as mainconfig
from users import users
from plugins import plugs
from persist import Persist
from errors import NoSuchBotType

## waveapi imports

from simplejson import load

## basic imports

import Queue
import os
import types
import time
import glob
import logging

## classes

class FleetBotAlreadyExists(Exception):
    pass


class Fleet(Persist):

    """
        a fleet contains multiple bots (list of bots).

    """

    def __init__(self):
        Persist.__init__(self, 'fleet')
        if not self.data.has_key('names'):
            self.data['names'] = []
        self.bots = []

    def loadall(self):
        """ load all bots. """
        for name in self.data.names:
            self.makebot(None, name)

    def avail(self):
        """ return available bots. """
        return self.data['names']

    def getfirstbot(self):
        """ return the first bot in the fleet. """
        return self.bots[0]

    def getfirstjabber(self):
        """ return the first jabber bot of the fleet. """
        for bot in self.bots:
            if bot.type == 'xmpp' or bot.type == 'jabber':
               return bot
        
    def size(self):
        """ return number of bots in fleet. """
        return len(self.bots)

    def settype(self, name, type):
        """ set the type of a bot. """
        cfg = Config('fleet' + os.sep + name + os.sep + 'config')
        cfg['name'] = name
        logging.warn("fleet - %s - setting type to %s" % (self.cfile, type))
        cfg.type = type
        cfg.save()

    def makebot(self, type=None, name=None, domain="", cfg={}):
        """ 
            create a bot .. use configuration if provided. 

            :param type: the type of the bot 
            :type type: string
            :param name: name of the bot
            :type name: string
            :param domain: domain to which the bot is connected
            :type domain: string
            :param cfg: configuration of the bot
            :type cfg: gozerlib.config.Config

        """
        logging.info('fleet - making %s (%s) bot - %s' % (type, name, str(cfg)))
        bot = None
        bot.name = name = name or 'default-%s' % type
        if not cfg:
            cfg = Config('fleet' + os.sep + name + os.sep + 'config')
            cfg['name'] = name 
        if not cfg.type and type:
            logging.warn("fleet - %s - setting type to %s" % (cfg.cfile, type))
            cfg.type = type
            cfg.save()
        if not cfg['type']:
            try:
                self.data['names'].remove(name)
                self.save()
            except ValueError:
                pass

            raise Exception("no bot type specified")
        if not cfg.owner:
            cfg.owner = mainconfig.owner
        if not cfg['domain'] and domain:
            cfg['domain'] = domain
            cfg.save()
        if not cfg:
            raise Exception("can't make config for %s" % name)

        type = type or cfg['type']

        # create bot based on type 
        if type == 'xmpp' or type == 'jabber':
            from gozerlib.gae.xmpp.bot import XMPPBot
            bot = XMPPBot(cfg)
        elif type == 'web':
            from gozerlib.gae.web.bot import WebBot
            bot = WebBot(cfg)
        elif type == 'wave':
            from gozerlib.gae.wave.bot import WaveBot
            dom = cfg.domain or domain
            bot = WaveBot(cfg, domain=dom)
        elif type == 'remote':
            from gozerlib.remote.bot import RemoteBot
            bot = RemoteBot(cfg)
        else:
            raise NoSuchBotType('%s bot .. unproper type %s' % (name, type))

        # set bot name and initialize bot
        if bot:
            if name and name not in self.data['names']:
                self.data['names'].append(name)
                self.save()
            self.addbot(bot)
            return bot

        # failed to created the bot
        raise Exception("can't make %s bot" % name)

    def makewavebot(self, domain, cfg={}):
        """
            create a bot .. use configuration if provided.

            :param name: the name of the bot
            :type name: string
            :param cfg: configuration file for the bot
            :type cfg: gozerlib.config.Config

        """
        logging.info('fleet - making %s (%s) wave bot - %s' % (domain, 'wave', str(cfg)))
        bot = None
        type = 'wave'
        name = domain
        if not cfg:
            cfg = Config('fleet' + os.sep + name + os.sep + 'config')
            cfg['name'] = domain
        if not cfg.owner:
            cfg.owner = mainconfig.owner
        if not cfg['domain']:
            cfg['domain'] = domain
            cfg.save()
        if not cfg.type:
            logging.warn("fleet - %s - setting type to %s" % (cfg.cfile, type))
            cfg.type = type
            cfg.save()
        if not cfg['type']:
            try:
                self.data['names'].remove(name)
                self.save()
            except ValueError:
                pass

            raise Exception("no bot type specified")
        if not cfg:
            raise Exception("can't make config for %s" % name)

        type = 'wave'

        # create bot based on type 
        from gozerlib.gae.wave.bot import WaveBot
        bot = WaveBot(cfg, domain=domain)

        # set bot name and initialize bot
        if bot:
            if name not in self.data['names']:
                self.data['names'].append(name)
                self.save()
            self.addbot(bot)
            return bot

        # failed to created the bot
        raise Exception("can't make %s bot" % name)

    def save(self):
        """ save fleet data and call save on all the bots. """
        Persist.save(self)
        for i in self.bots:
            try:
                i.save()
            except Exception, ex:
                handle_exception()

    def list(self):
        """ return list of bot names. """
        result = []
        for i in self.bots:
            result.append(i.name)

        return result

    def stopall(self):
        """ call stop() on all fleet bots. """
        for i in self.bots:
            try:
                i.stop()
            except:
                handle_exception()

    def byname(self, name):
        """ return bot by name. """
        for i in self.bots:
            if name == i.name:
                return i

    def bydomain(self, domain):
        """ return bot by domain. """
        for i in self.bots:
            if domain == i.domain:
                return i

        return self.makewavebot(domain)

    def replace(self, name, bot):
        """ replace bot with a new bot. """
        for i in range(len(self.bots)):
            if name == self.bots[i].name:
                self.bots[i] = bot
                return

    def addbot(self, bot):
        """
            add a bot to the fleet .. remove all existing bots with the 
            same name.
        """
        if bot:
            for i in range(len(self.bots)-1, -1, -1):
                if self.bots[i].name == bot.name:
                    logging.debug('fleet - removing %s from fleet' % bot.name)
                    del self.bots[i]

            logging.debug('fleet - adding %s' % bot.name)
            self.bots.append(bot)
            return True

        return False

    def delete(self, name):
        """ delete bot with name from fleet. """
        for i in self.bots:
            if i.name == name:
                i.exit()
                self.remove(i)
                i.cfg['enable'] = 0
                i.cfg.save()
                logging.debug('fleet - %s disabled' % i.name)
                return True

        return False


    def remove(self, bot):
        """ delete bot by object. """
        try:
            self.bots.remove(bot)
            return True
        except ValueError:
            return False

    def exit(self, name=None):
        """ call exit on all bots. """
        if not name:
            threads = []
            for i in self.bots:
                i.exit()
            return

        for i in self.bots:
            if i.name == name:
                try:
                    i.exit()
                except:
                    handle_exception()
                self.remove(i)
                return True

        return False

    def cmnd(self, event, name, cmnd):
        """
            do command on a bot.

            :param event: event to pass on to the dispatcher
            :type event: gozerlib.event.EventBase
            :param name: name of the bot to pass on to the dispatcher
            :type name: string
            :param cmnd: command to execute on the fleet bot
            :type cmnd: string
            :rtype: list of strings

        """
        bot = self.byname(name)
        if not bot:
            return 0

        # create an event and dispatch it
        from gozerlib.eventbase import EventBase
        j = plugs.clonedevent(bot, event)
        j.onlyqueues = True
        j.txt = cmnd
        q = Queue.Queue()
        j.queues = [q]
        j.speed = 3
        plugs.trydispatch(bot, j)
        result = waitforqueue(q)

        if not result:
            return

        res = ["[%s]" % bot.name, ]
        res += result
        event.reply(res)
        return res

    def cmndall(self, event, cmnd):
        """
            do a command on all bots.

            :param event: event to pass on to dispatcher
            :type event: gozerlib.eventbase.EventBase
            :param cmnd: the command string to execute
            :type cmnd: string

        """
        for i in self.bots:
            self.cmnd(event, i.name, cmnd)

    def broadcast(self, txt):
        """ broadcast txt to all bots. """
        for i in self.bots:
            i.broadcast(txt)

## defines

fleet = Fleet()
