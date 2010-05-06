# gozerlib/socklib/xmpp/message.py
#
#

""" jabber message definition .. types can be normal, chat, groupchat, 
    headline or  error
"""

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.utils.trace import whichmodule
from gozerlib.utils.generic import toenc, fromenc, jabberstrip
from gozerlib.utils.locking import lockdec
from gozerlib.eventbase import EventBase
from gozerlib.config import cfg
from gozerlib.channelbase import ChannelBase
from gozerlib.errors import BotNotSetInEvent

## xmpp imports

from core import XMLDict

## basic imports

import types
import time
import thread
import logging

## locks
replylock = thread.allocate_lock()
replylocked = lockdec(replylock)

if cfg['dotchars']:
    dotchars = cfg['dotchars']
else:
    dotchars = ' .. '

class Message(XMLDict):

    """ jabber message object. """

    def __init__(self, nodedict={}):
        XMLDict.__init__(self, nodedict)
        self.element = "message"
        self.jabber = True
        self.cmnd = "MESSAGE"
        self.cbtype = "MESSAGE"
        self.bottype = "xmpp"
  
    def __copy__(self):
        return Message(self)

    def __deepcopy__(self, bla):
        return Message(self)

                 
    #@replylocked
    def reply(self, txt, result=None, nick=None, dot=False, nritems=False, nr=False, fromm=None, private=False):
        """ reply txt. """
        if result == []:
            return
        restxt = ""

        if type(result) == types.DictType:
            for i, j in result.iteritems():
                if type(j) == types.ListType:
                    try:
                        z = dotchars.join(j)
                    except TypeError:
                        z = unicode(j)
                else:
                    z = j
                if dot == True:
                    restxt += "%s: %s %s " % (i, z, dotchars)
                elif dot:
                    restxt += "%s: %s %s " % (i, z, dot)
                else:
                    restxt += "%s: %s " % (i, z)

            if restxt:
                if dot == True:
                    restxt = restxt[:-6]
                elif dot:
                    restxt = restxt[:-len(dot)]
        lt = False
        if type(txt) == types.ListType and not result:
            result = txt
            origtxt = ""
            lt = True
        else:
            origtxt = txt
        if result:
            lt = True

        if self.queues:
            for i in self.queues:
                if lt:
                    for j in result:
                        i.put_nowait(j)
                else:
                    i.put_nowait(txt)
            if self.onlyqueues:
                return

        pretxt = origtxt
        if lt and not restxt:
            res = []
            for i in result:
                if type(i) == types.ListType or type(i) == types.TupleType:
                    try:
                        res.append(dotchars.join(i))
                    except TypeError:
                        res.append(unicode(i))
                else:
                    res.append(i)
            result = res
            if nritems:
                if len(txt) > 1:
                    pretxt = "(%s items) .. " % len(result)
            txtlist = [unicode(i) for i in result]
            if not nr is False:
                try:
                    start = int(nr)
                except ValueError:
                    start = 0
                txtlist2 = []
                teller = start
                for i in txtlist:
                    txtlist2.append("%s) %s" % (teller, i))
                    teller += 1
                txtlist = txtlist2
            if dot == True:
                restxt = dotchars.join(txtlist)
            elif dot:
                restxt = dot.join(txtlist)
            else:
                restxt = ' '.join(txtlist)

        if pretxt:
            restxt = pretxt + restxt

        txt = jabberstrip(restxt)

        if not txt:
            return

        what = txt
        txtlist = []
        start = 0
        end = 900
        length = len(what)

        for i in range(length/end+1):
            endword = what.find(' ', end)
            if endword == -1:
                endword = end
            txtlist.append(what[start:endword])
            start = endword
            end = start + 900

        size = 0

        # see if we need to store output in less cache
        if len(txtlist) > 1:
            self.less.add(self.userhost, txtlist)
            size = len(txtlist) - 1
            result = txtlist[:1][0]
            if size:
                result += " (+%s)" % size
        else:
            result = txtlist[0]

        #try:
        #    to = self.options['--to']
        #except KeyError:
        #    to = None
        to = None
        outtype = self.type

        if not self.bot:
            raise BotNotSetInEvent("xmpp.message")

        if to and to in self.bot.state['joinedchannels']:
            outtype = 'groupchat' 
            self.groupchat = True
            self.msg = False

        repl = Message({'from': self.me, 'to': to or self.jid, 'type': outtype, 'txt': result})

        if self.groupchat:
            if self.resource == self.bot.nick:
                return
            if to:
                pass
            elif nick:
                repl.type = 'chat'
            elif private:
                repl.to = self.userhost
            elif self.printto:
                repl.to = self.printto
            else:
                repl.to = self.channel

        if nick:
            repl.type = 'normal'
        elif not repl.type:
            repl.type = 'chat'

        self.bot.send(repl)

    def parse(self, bot=None):
        """ set ircevent compat attributes. """
        self.bot = bot
        self.jidchange = False
        self.cmnd = 'Message'
        try:
            self.resource = self.fromm.split('/')[1]
        except IndexError:
            pass

        self.channel = self['fromm'].split('/')[0]
        self.chan = ChannelBase(self.channel)
        self.origchannel = self.channel
        self.nick = self.resource
        self.jid = self.fromm
        self.ruserhost = self.jid
        self.userhost = self.jid
        self.stripped = self.jid.split('/')[0]
        self.printto = self.channel

        for node in self.subelements:
            try:
                self.txt = node.body.data
            except (AttributeError, ValueError):
                continue

        if self.txt:
            self.usercmnd = self.txt.split()[0]
        else:
            self.usercmnd = ""
        self.origtxt = self.txt
        self.time = time.time()

        if self.type == 'groupchat':
            self.groupchat = True
            if self.jidchange:
                self.userhost = self.stripped
        else:
            self.groupchat = False
            self.userhost = self.stripped

        self.msg = not self.groupchat
        self.makeargs()

    def errorHandler(self):
        """ dispatch errors to their handlers. """
        try:
            code = self.get('error').code
        except Exception, ex:
            handle_exception()
        try:
            method = getattr(self, "handle_%s" % code)
            if method:
                logging.error('sxmpp.core - dispatching error to handler %s' % str(method))
                method(self)
        except AttributeError, ex:
            logging.error('sxmpp.core - unhandled error %s' % code)
        except:
            handle_exception()
