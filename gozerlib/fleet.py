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
from errors import NoSuchBotType, BotNotEnabled
from threads import start_new_thread
from eventhandler import mainhandler
from datadir import datadir
from utils.name import stripname

## waveapi imports

from simplejson import load

## basic imports

import Queue
import os
import types
import time
import glob
import logging
import threading

## classes

class FleetBotAlreadyExists(Exception):
    pass


class Fleet(Persist):

    """
        a fleet contains multiple bots (list of bots).

    """

    def __init__(self):
        Persist.__init__(self, datadir + os.sep + 'fleet' + os.sep + 'fleet.main')
        if not self.data.has_key('names'):
            self.data['names'] = []
        if not self.data.has_key('types'):
            self.data['types'] = {}
        self.startok = threading.Event()
        self.bots = []

    def loadall(self, names=[]):
        """ load all bots. """ 
        target = names or self.data.names
        if not target:
            logging.error("fleet - no bots in fleet")
        else:
            logging.warning("fleet - loading %s" % ", ".join(target))

        for name in target:
            if not name:
                logging.debug("fleet - name is not set")
                continue
            try:
                self.makebot(self.data.types[name], name)
            except BotNotEnabled:
                pass
            except KeyError:
                logging.error("no type know for %s bot" % name)
            except Exception, ex:
                handle_exception()

    def avail(self):
        """ return available bots. """
        return self.data['names']

    def getfirstbot(self):
        """ return the first bot in the fleet. """
        return self.bots[0]

    def getfirstjabber(self, isgae=False):
        """ return the first jabber bot of the fleet. """
        for bot in self.bots:
            
            if isgae:
                if (bot.type == 'xmpp' or bot.type == 'jabber'): 
                    return bot
            else:
                if bot.type == 'sxmpp':
                    return bot
        
    def size(self):
        """ return number of bots in fleet. """
        return len(self.bots)

    def settype(self, name, type):
        """ set the type of a bot. """
        cfg = Config('fleet' + os.sep + stripname(name) + os.sep + 'config')
        cfg['name'] = name
        logging.debug("fleet - %s - setting type to %s" % (self.cfile, type))
        cfg.type = type
        cfg.save()

    def makebot(self, type, name, domain="", cfg={}):
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
        if cfg:
            logging.warn('fleet - making %s (%s) bot - %s' % (type, name, cfg.dump()))
        bot = None
        if not cfg:
            cfg = Config('fleet' + os.sep + stripname(name) + os.sep + 'config')
            cfg['name'] = name
        if not cfg.type and type:
            logging.debug("fleet - %s - setting type to %s" % (cfg.cfile, type))
            cfg.type = type
        if not cfg['type']:
            try:
                self.data['names'].remove(name)
                self.save()
            except ValueError:
                pass

            raise Exception("no bot type specified")
        if not cfg.owner:
            cfg.owner = mainconfig.owner
        if not cfg.domain and domain:
            cfg.domain = domain
        if not cfg:
            raise Exception("can't make config for %s" % name)
        cfg.save()
        if cfg.disable:
            logging.warn("fleet - %s bot is disabled" % name)
            raise BotNotEnabled(name)
        # create bot based on type 
        if type == 'xmpp' or type == 'jabber':
            try:
                from gozerlib.gae.xmpp.bot import XMPPBot
                bot = XMPPBot(cfg)
            except ImportError:
                from gozerlib.socklib.xmpp.bot import SXMPPBot          
                bot = SXMPPBot(cfg)
        elif type == 'sxmpp':
            from gozerlib.socklib.xmpp.bot import SXMPPBot
            bot = SXMPPBot(cfg)
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
        elif type == 'irc':
            from gozerlib.socklib.irc.bot import IRCBot
            bot = IRCBot(cfg)
        elif type == 'console':
            from gozerlib.console.bot import ConsoleBot
            bot = ConsoleBot(cfg)
        elif type == 'base':
            from gozerlib.botbase import BotBase
            bot = BotBase(cfg)
        else:
            raise NoSuchBotType('%s bot .. unproper type %s' % (name, type))

        # set bot name and initialize bot
        if bot:
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
        logging.debug('fleet - making %s (%s) wave bot - %s' % (domain, 'wave', str(cfg)))
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
            logging.debug("fleet - %s - setting type to %s" % (cfg.cfile, type))
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
                return True

    def enable(self, cfg):
        if cfg.botname and cfg.botname not in self.data['names']:
            self.data['names'].append(cfg.botname)
            self.data['types'][cfg.botname] = cfg.type
            self.save()
        return True

    def addbot(self, bot):
        """
            add a bot to the fleet .. remove all existing bots with the 
            same name.
        """
        for i in range(len(self.bots)-1, -1, -1):
            if self.bots[i].name == bot.botname:
                logging.debug('fleet - removing %s from fleet' % bot.botname)
                del self.bots[i]

        logging.info('fleet - adding %s' % bot.botname)
        self.bots.append(bot)
        if bot.botname and bot.botname not in self.data['names']:
            self.data['names'].append(bot.botname)
            self.data['types'][bot.botname] = bot.type
            self.save()
        return True

    def delete(self, name):
        """ delete bot with name from fleet. """
        for bot in self.bots:
            if bot.botname == name:
                bot.exit()
                self.remove(i)
                bot.cfg['disable'] = 1
                bot.cfg.save()
                logging.debug('fleet - %s disabled' % bot.botname)
                return True

        return False


    def remove(self, bot):
        """ delete bot by object. """
        try:
            self.bots.remove(bot)
            return True
        except ValueError:
            return False

    def exit(self, name=None, jabber=False):
        """ call exit on all bots. """
        if not name:
            threads = []
            for bot in self.bots:
                if jabber and bot.type != 'sxmpp' and bot.type != 'jabber':
                    continue
                threads.append(start_new_thread(bot.exit, ()))
            for thread in threads: 
                thread.join()
            return

        for bot in self.bots:
            if bot.botname == name:
                if jabber and bot.type != 'sxmpp' and bot.type != 'jabber':
                    continue
                try:
                    bot.exit()
                except:
                    handle_exception()
                self.remove(bot)
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

        res = ["[%s]" % bot.botname, ]
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
        for bot in self.bots:
            self.cmnd(event, bot.botname, cmnd)

    def broadcast(self, txt):
        """ broadcast txt to all bots. """
        for bot in self.bots:
            bot.broadcast(txt)

    def startall(self):
        for bot in self.bots:
            start_new_thread(bot.start, ())

    def resume(self, sessionfile):
        """ resume bot from session file. """
        # read JSON session file
        session = load(open(sessionfile))

        #  resume bots in session file
        for name in session['bots'].keys():
            reto = None
            if session['name'] == name:
                reto = session['channel']
            start_new_thread(self.resumebot, (name, session['bots'][name], reto))

        # allow 5 seconds for bots to resurrect
        time.sleep(5)

        # set start event
        self.startok.set()

    def resumebot(self, botname, data={}, printto=None):
        """
            resume individual bot.

            :param botname: name of the bot to resume
            :type botname: string
            :param data: resume data
            :type data: dict
            :param printto: whom to reply to that resuming is done
            :type printto: nick or JID
        """
        logging.warn("fleet - resuming %s bot" % botname)
        # see if we need to exit the old bot
        oldbot = self.byname(botname)
        if oldbot and data['type'] == "sxmpp":
            oldbot.exit()
        cfg = Config('fleet' + os.sep + stripname(botname) + os.sep + 'config')

        # make the bot and resume (IRC) or reconnect (Jabber)
        logging.warn("fleet - resuming %s bot .. %s" % (botname, str(data)))
        bot = self.makebot(data['type'], botname)
        if data['type'] != "sxmpp":
            if oldbot:
                self.replace(oldbot, bot)
            bot._resume(data, printto)
            bot.start(False)
        else:
            start_new_thread(bot.start, ())

## defines

fleet = Fleet()
