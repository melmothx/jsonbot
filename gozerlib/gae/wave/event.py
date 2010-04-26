# gozerlib/wave/event.py
#
#

""" google wave events. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.exception import handle_exception
from gozerlib.gae.utils.auth import finduser
from gozerlib.gae.wave.waves import Wave


## basic imports

import logging
import cgi
import re
import time

## defines

findurl = re.compile(u"(http://.*)?")

class NotConnected(Exception):

    pass

class WaveEvent(EventBase):


    """ a wave event. """

    def __init__(self):
        EventBase.__init__(self)
        self.type = "wave"
        self.msg = False
        self.target = None
        self.roottarget = None
        self.rootreply = None
        self.gadget = None
        self.result = []

    def parse(self, bot, event, wavelet):

        """ parse properties and context into a WaveEvent. """

        #logging.debug("WaveEvent created")
        self.bot = bot
        self.eventin = event
        self.wavelet = wavelet
        #logging.debug("eventin: %s" % dir(self.eventin))
        #logging.debug("wavelet: %s" % dir(self.wavelet))
        self.waveid = self.wavelet._wave_id
        self.blipid = self.eventin.blip_id
        self.blip = self.eventin.blip
        self.chan = Wave(self.waveid)
        self.chan.parse(self.eventin, self.wavelet)

        if not self.blip:
            logging.warn("can't get blip id: %s" % self.blipid)
            self.contributors = []
            self.txt = ""
            self.cmnd = ""
            self.userhost = ""
            self.ispoller = False
        else:
            #logging.debug("blip: %s" % dir(self.blip))
            self.contributors = self.blip._contributors
            self.origtxt = self.blip._content
            self.txt = self.origtxt.strip()
            if len(self.txt) >= 2:
                self.usercmnd = self.txt[1:].split()[0]
            else:
                self.usercmnd = None
          #logging.debug("blipdata: %s" % self.txt)
            self.userhost = self.blip._creator
            self.elements = self.blip._elements
            #logging.debug("elements: %s" % unicode(self.elements))

            for nr, elem in self.elements.iteritems():
                logging.debug("wave - element - %s - %s" % (str(elem), dir(elem)))
                if elem.get('ispoller') == 'yes':
                    self.ispoller = True
                if elem.get('gadgetcmnd') == 'yes':
                    self.cbtype = "GADGETCMND"
                    logging.debug("wave.event - gadgetcmnd - %s" % str(elem))
                    self.txt = u"!" + elem.get("cmnd")
                    self.channel = self.waveid = elem.get("waveid")
                    self.gadgetnr = nr
                    self.cmndhow = elem.get('how')
                    self.userhost = elem.get('who')
        self.auth = self.userhost
        logging.debug("wave - event - auth is %s" % self.auth)
        self.root = wavelet
        self.rootblipid = wavelet._root_blip.blip_id
        #logging.debug("rootblip: %s" % self.rootblipid)
        self.rootblip = wavelet._root_blip
        #logging.debug("rootblip: %s" % dir(self.rootblip))
        logging.debug("root: %s" % dir(self.root))
        #logging.debug("raw_data: %s" % unicode(self.root._raw_data))
        self.raw_data = self.root._raw_data
        self.domain = self.wavelet.domain
        self.channel = self.waveid
        self.origin = self.channel
        self.title = self.root._title or self.channel 
        self.cbtype = event.type

        if 'sandbox' in self.waveid:
            self.url = "https://wave.google.com/a/wavesandbox.com/#restored:wave:%s" % self.waveid.replace('w+','w%252B')
        else:
            self.url = "https://wave.google.com/wave/#restored:wave:%s" % self.waveid.replace('w+','w%252B')

        self.makeargs()        
        logging.warn(u'wave - in - %s - %s - %s' % (self.title, self.userhost, self.txt))

    def __deepcopy__(self, a):

        """ deepcopy a wave event. """

        e = WaveEvent()
        e.copyin(self)
        return e

    def _raw(self, outtxt, root=None):

        """ send raw text to the server .. creates a blip on the root. """

        pass
        #logging.info(u"wave - out - %s - %s" % (self.userhost, outtxt))
        #self.append(outtxt)
        #self.bot.outmonitor(self.origin, self.channel, outtxt)

    def toppost(self, txt):
        reply = self.rootblip.reply()
        reply.append(txt)
        if self.chan:
            self.chan.data.seenblips += 1
            self.chan.data.lastedited = time.time()
        return reply

    def insert_root(self, item):
        reply = self.rootblip.append(item)
        if self.chan:
            self.chan.data.seenblips += 1
            self.chan.data.lastedited = time.time()
        return self

    def set_title(self, title, cloned=False):
        if cloned and self.chan and self.chan.data.nrcloned:
            title = "#".join(title.split("#")[:-1])
            title += "#%s" % str(self.chan.data.nrcloned)

        logging.warn("wave - setting title - %s" % title)
        self.root._set_title(title)
        return self

    def append(self, item, annotations=None):

        if not self.target and self.blip:
            self.target = self.blip.reply()
        
        self.result.append(unicode(item))
        try:
            self.target.append(item)
        except Exception, ex:
            handle_exception()

        logging.debug("wave - append - annotations are %s" % str(annotations))
        if annotations:
            for ann in annotations:
                if ann[0]:
                    try:
                        self.target.range(ann[0], ann[1]).annotate(ann[2], ann[3])
                    except Exception, ex:
                        handle_exception()

        if self.chan:
            self.chan.data.seenblips += 1
            self.chan.data.lastedited = time.time()

        return self

    def append_root(self, item , annotations=None):

        if not self.roottarget:
            self.roottarget = self.rootblip.reply()

        self.roottarget.append(item)
        self.result.append(unicode(item))

        if self.chan:
            self.chan.data.seenblips += 1
            self.chan.data.lastedited = time.time()

        return self.roottarget

    def appendtopper(self, item):
        self.rootblip.append(item)
        self.result.append(unicode(item))

        if self.chan:
            self.chan.data.seenblips += 1
            self.chan.data.lastedited = time.time()

        return self.rootblip

    def reply(self, txt, resultlist=[], nritems=False, dot=", ", *args, **kwargs):

        """ reply to blip. """

        if self.checkqueues(resultlist):
            return

        outtxt = self.makeresponse(txt, resultlist, nritems, dot, *args, **kwargs)

        if not outtxt:
            return
        self.result.append(unicode(outtxt))

        #self.doc.SetText(cgi.escape(outtxt))
        (res1, res2) = self.less(outtxt)
        self.write(res1)
        if res2:
            self.write(res2)

    def replyroot(self, txt, resultlist=[], nritems=False, root=None, *args, **kwargs):

        """ reply to wave root. """

        if self.checkqueues(resultlist):
            return

        if resultlist:
            outtxt = txt + u" " + u' .. '.join(resultlist)
        else:
            outtxt = txt

        if not outtxt:
            return
        self.result.append(unicode(outtxt))

        logging.debug("wave - reply root - %s - %s" % (self.root, root))
        (res1, res2) = self.less(outtxt)
        self.write_root(res1, root)
        if res2:
            self.write_root(res2, root)

    def write(self, outtxt, end="\n"):

        """ write outtxt to the server. """

        logging.warn(u"wave - out - %s - %s" %  (self.userhost, unicode(outtxt)))

        try:
            annotations = []
            for url in re.findall(findurl, outtxt):
                start = outtxt.find(url.strip())
                if start:
                    annotations.append((start+1, start+len(url), "link/manual", url.strip()))
        except Exception, ex:
            handle_exception()

        if self.gadgetnr:
            if self.cmndhow == 'output':
                self.blip.at(self.gadgetnr).update_element({'text': outtxt, 'target': self.userhost})
            elif self.cmndhow == 'status':
                self.blip.at(self.gadgetnr).update_element({'status': outtxt, 'target': self.userhost})
        else:
            self.append(outtxt + end , annotations)

        self.replied = True
        self.bot.outmonitor(self.origin, self.channel, outtxt, self)

    def write_root(self, outtxt, end="\n", root=None):

        """ write to the root of a wave. """

        logging.warn(u"wave - out - %s - %s" %  (self.userhost, unicode(outtxt)))
        self.append_root(outtxt + end)
        self.replied = True
        self.bot.outmonitor(self.origin, self.channel, outtxt, self)

    def submit(self):
        self.bot.submit(self.wavelet)
