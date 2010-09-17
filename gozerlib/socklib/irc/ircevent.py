# gozerbot/ircevent.py
#
#
# http://www.irchelp.org/irchelp/rfc/rfc2812.txt

""" an ircevent is extracted from the IRC string received from the server. """

__copyright__ = 'this file is in the public domain'

## gozerbot imports

from gozerlib.utils.generic import toenc, fromenc, strippedtxt
from gozerlib.socklib.utils.generic import fix_format, stripident, makeargrest
from gozerlib.eventbase import EventBase
from gozerlib.config import cfg as config
from gozerlib.channelbase import ChannelBase

## basic imports

import time
import re
import types
import copy
import logging

## defines

cpy = copy.deepcopy

try:
    dotchars = config['dotchars']
    if not dotchars:
        dotchars = ' .. '
except KeyError:
    dotchars = ' .. '

## functions

def makeargrest(ievent):

    """ create ievent.args and ievent.rest .. this is needed because \
         ircevents might be created outside the parse() function.
    """ 

    if not ievent.txt:
        return

    try:
        ievent.args = ievent.txt.split()[1:]
    except ValueError:
        ievent.args = []

    try:
        cmnd, ievent.rest = ievent.txt.split(' ', 1)
    except ValueError:
        ievent.rest = ""   

    ievent.command = ievent.txt.split(' ')[0]

## classes

class Ircevent(EventBase):

    """ represents an IRC event. """

    def __deepcopy__(self, bla):
        e = Ircevent()
        e.copyin(self)
        return e

    def toirc(self):
        pass

    def parse(self, bot, rawstr):

        """ parse raw string into ircevent. """

        self.bottype = "irc"
        self.bot = bot
        bot.nrevents += 1 
        self.ttl = 2
        rawstr = rawstr.rstrip()
        splitted = re.split('\s+', rawstr)

        # check if there is a prefix (: in front)
        if not rawstr[0] == ':':
            # no prefix .. 1st word is command
            splitted.insert(0, ":none!none@none")
            rawstr = ":none!none@none " + rawstr

        self.prefix = splitted[0][1:]

        # get nick/userhost
        nickuser = self.prefix.split('!')
        if len(nickuser) == 2:
            self.nick = nickuser[0]
            if self.bot.cfg['stripident'] or config['stripident']:
                self.userhost = stripident(nickuser[1])
            else:
                self.userhost = nickuser[1]

        # set command
        self.cmnd = splitted[1]
        self.cbtype = self.cmnd

        # split string based of postfix count .. nr of items ater the command
        if pfc.has_key(self.cmnd):
            self.arguments = splitted[2:pfc[self.cmnd]+2]
            txtsplit = re.split('\s+', rawstr, pfc[self.cmnd]+2)
            self.txt = txtsplit[-1]
        else:
            self.arguments = splitted[2:]

        # 1st argument is target
        if self.arguments:
            self.target = self.arguments[0]
        self.postfix = ' '.join(self.arguments)

        # check if target is text
        if self.target and self.target.startswith(':'):
            self.txt = ' '.join(self.arguments)

        # strip strarting ':' from txt
        if self.txt:
            if self.txt[0] == ":":
                self.txt = self.txt[1:]
            if self.txt:
                self.usercmnd = self.txt.split()[0]

        #logging.debug("irc - event - %s %s %s" % (self.cmnd, self.arguments, self.txt))

        # set ircevent attributes
        if self.cmnd == 'PING':
            self.speed = 9
        if self.cmnd == 'PRIVMSG':
            self.channel = self.arguments[0]
            if '\001' in self.txt:
                self.isctcp = True
        elif self.cmnd == 'JOIN' or self.cmnd == 'PART':
            if self.arguments:
                self.channel = self.arguments[0]
            else:
                self.channel = self.txt
        elif self.cmnd == 'MODE':
            self.channel = self.arguments[0]
        elif self.cmnd == 'TOPIC':
            self.channel = self.arguments[0]
        elif self.cmnd == 'KICK':
            self.channel = self.arguments[0]
        elif self.cmnd == '353':
            self.channel = self.arguments[2]
        elif self.cmnd == '324':
            self.channel = self.arguments[1]
        if self.userhost:
            # userhost before possible stripident
            self.ruserhost = self.userhost
            # jabber compat .. this is userhost on irc
            self.stripped = self.userhost
            # determine user
            #self.user = stripident(self.userhost).split('@')[0]
            self.auth = self.userhost

        self.origtxt = self.txt
        if self.channel:
            self.channel = self.channel.strip()
            self.origchannel = self.channel
            self.chan = ChannelBase(self.channel)

        # show error
        try:
            nr = int(self.cmnd)
            if nr > 399 and not nr == 422:
                logging.error('irc - %s - %s - %s' % (self.cmnd, self.arguments, self.txt))
        except ValueError:
            pass
        self.printto = self.channel 
        makeargrest(self)
        return self

    def reply(self, txt, result=[], to="", dot=", ", extend=15, raw=False):
        if self.checkqueues(result):
            return
        if result:
            txt = u"<b>" + txt + u"</b>"
        restxt = self.makeresponse(txt, result, dot)
        if not raw:
            restxt = strippedtxt(restxt)
        restxt = self.bot.normalize(restxt)
        if self.isdcc:
            self.sock.send(restxt)
            self.sock.send("\n")
            return
        #res1, nritems = self.less(restxt, 365+extend)
        res1 = restxt
        target = to or self.printto
        self.bot.out(target, res1, 'msg')
        self.bot.outmonitor(self.userhost, target, res1, self)

## postfix count aka how many arguments

pfc = {}
pfc['NICK'] = 0
pfc['QUIT'] = 0
pfc['SQUIT'] = 1
pfc['JOIN'] = 0
pfc['PART'] = 1
pfc['TOPIC'] = 1
pfc['KICK'] = 2
pfc['PRIVMSG'] = 1
pfc['NOTICE'] = 1
pfc['SQUERY'] = 1
pfc['PING'] = 0
pfc['ERROR'] = 0
pfc['AWAY'] = 0
pfc['WALLOPS'] = 0
pfc['INVITE'] = 1
pfc['001'] = 1
pfc['002'] = 1
pfc['003'] = 1
pfc['004'] = 4
pfc['005'] = 15
pfc['302'] = 1
pfc['303'] = 1
pfc['301'] = 2
pfc['305'] = 1
pfc['306'] = 1
pfc['311'] = 5
pfc['312'] = 3
pfc['313'] = 2
pfc['317'] = 3
pfc['318'] = 2
pfc['319'] = 2
pfc['314'] = 5
pfc['369'] = 2
pfc['322'] = 3
pfc['323'] = 1
pfc['325'] = 3
pfc['324'] = 4
pfc['331'] = 2
pfc['332'] = 2
pfc['341'] = 3
pfc['342'] = 2
pfc['346'] = 3
pfc['347'] = 2
pfc['348'] = 3
pfc['349'] = 2
pfc['351'] = 3
pfc['352'] = 7
pfc['315'] = 2
pfc['353'] = 3
pfc['366'] = 2
pfc['364'] = 3
pfc['365'] = 2
pfc['367'] = 2
pfc['368'] = 2
pfc['371'] = 1
pfc['374'] = 1
pfc['375'] = 1
pfc['372'] = 1
pfc['376'] = 1
pfc['381'] = 1
pfc['382'] = 2
pfc['383'] = 5
pfc['391'] = 2
pfc['392'] = 1
pfc['393'] = 1
pfc['394'] = 1
pfc['395'] = 1
pfc['262'] = 3
pfc['242'] = 1
pfc['235'] = 3
pfc['250'] = 1
pfc['251'] = 1
pfc['252'] = 2
pfc['253'] = 2
pfc['254'] = 2
pfc['255'] = 1
pfc['256'] = 2
pfc['257'] = 1
pfc['258'] = 1
pfc['259'] = 1
pfc['263'] = 2
pfc['265'] = 1
pfc['266'] = 1
pfc['401'] = 2
pfc['402'] = 2
pfc['403'] = 2
pfc['404'] = 2
pfc['405'] = 2
pfc['406'] = 2
pfc['407'] = 2
pfc['408'] = 2
pfc['409'] = 1
pfc['411'] = 1
pfc['412'] = 1
pfc['413'] = 2
pfc['414'] = 2
pfc['415'] = 2
pfc['421'] = 2
pfc['422'] = 1
pfc['423'] = 2
pfc['424'] = 1
pfc['431'] = 1
pfc['432'] = 2
pfc['433'] = 2
pfc['436'] = 2
pfc['437'] = 2
pfc['441'] = 3
pfc['442'] = 2
pfc['443'] = 3
pfc['444'] = 2
pfc['445'] = 1
pfc['446'] = 1
pfc['451'] = 1
pfc['461'] = 2
pfc['462'] = 1
pfc['463'] = 1
pfc['464'] = 1
pfc['465'] = 1
pfc['467'] = 2
pfc['471'] = 2
pfc['472'] = 2
pfc['473'] = 2
pfc['474'] = 2
pfc['475'] = 2
pfc['476'] = 2
pfc['477'] = 2
pfc['478'] = 3
pfc['481'] = 1
pfc['482'] = 2
pfc['483'] = 1
pfc['484'] = 1
pfc['485'] = 1
pfc['491'] = 1
pfc['501'] = 1
pfc['502'] = 1
pfc['700'] = 2

                
# default event used to initialise events
defaultevent = EventBase()
