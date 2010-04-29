# gozerlib/wave/waves.py
#
#

""" class to repesent a wave. """

## gozerlib imports

from gozerlib.channelbase import ChannelBase
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.locking import lockdec

## simplejson imports

from simplejson import dumps

## google imports

import google

## basic imports

import logging
import copy
import os
import time
import re
import thread

## defines

findurl = re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]'\\.}>\\),\\\"]")
cpy = copy.deepcopy

saylock = thread.allocate_lock()
saylocked = lockdec(saylock)

## classes

class Wave(ChannelBase):

    """ a wave is seen as a channel. """

    def __init__(self, waveid):
        ChannelBase.__init__(self, 'gozerdata' + os.sep + 'waves' + os.sep + waveid)
        self.data.seenblips = self.data.seenblips or 0
        self.data.threshold = self.data.threshold or -1
        self.data.nrcloned = self.data.nrcloned or 0
        self.data.waveid = waveid
        self.wavelet = None
        self.event = None
        logging.debug("created wave with id: %s" % waveid)

    def parse(self, event, wavelet):
        """ parse event into a Wave. """
        self.data.json_data = wavelet.serialize()
        self.data.title = wavelet._title
        self.data.waveletid = wavelet._wavelet_id
        self.wavelet = wavelet
        self.event = event
        logging.debug("parsed %s (%s) channel" % (self.data.waveid, self.data.title))
        return self

    def set_title(self, title, cloned=False):
        """ set title of wave. """
        self.event.set_title(title, cloned)

    def clone(self, bot, event, title=None, report=False, participants=[]):
        """ clone the wave into a new one. """
        if participants:
            parts = participants
        else:
            parts = list(event.root.participants)
        newwave = bot.newwave(event.domain, parts)
        logging.warn("wave - clone - populating wave with %s" % str(parts))
        for id in parts:
            newwave.participants.add(id)
        if title:
            if '#' in title:
                title = "#".join(title.split("#")[:-1])
                title += "#%s" % str(self.data.nrcloned + 1)
            else:
                title += " - #%s" % str(self.data.nrcloned + 1)
            newwave._set_title(title)

        if report:
            try:
                txt = '\n'.join(event.rootblip.text.split('\n')[2:])
            except IndexError:
                txt = event.rootblip.text

            newwave._root_blip.append(u'%s\n' % txt)

            for element in event.rootblip.elements:
                if element.type == 'GADGET':
                    newwave._root_blip.append(element)

            blip = newwave.reply()
            blip.append("\nthis wave is cloned from %s\n" % event.url)
        else:
            newwave._root_blip.append("PROTECTED WAVE")

        wavelist = bot.submit(newwave)
        logging.warn("wave - clone - %s - submit returned %s" % (list(newwave.participants), str(wavelist)))

        if not wavelist:
            logging.warn("submit of new wave failed")
            return

        try:
            waveid = None
            for item in wavelist:
                try:
                    waveid = item['data']['waveId']
                except (KeyError, ValueError):
                    continue
        
            logging.warn("wave - newwave id is %s" % waveid)
            if not waveid:
                logging.error("can't extract waveid from submit data")
                return

            if waveid and 'sandbox' in waveid:
                url = "https://wave.google.com/a/wavesandbox.com/#restored:wave:%s" % waveid.replace('w+','w%252B')
            else:
                url = "https://wave.google.com/wave/#restored:wave:%s" % waveid.replace('w+','w%252B')

            oldwave = Wave(event.waveid)
            oldwave.data.threshold = -1
            oldwave.save()

            wave = Wave(waveid)
            wave.parse(event, newwave)
            wave.data.json_data = newwave.serialize()
            wave.data.threshold = self.data.threshold or 200
            wave.data.nrcloned = self.data.nrcloned + 1
            wave.data.url = url
            wave.save()


        except Exception, ex:
            handle_exception()
            return

        return wave

    @saylocked
    def say(self, bot, txt):
        """ output some txt to the wave. """
        if self.data.json_data:
            logging.debug("wave - say - using BLIND - %s" % self.data.json_data) 
            wavelet = bot.blind_wavelet(self.data.json_data)
        else:
            logging.info("did not join channel %s" % self.id)
            return
        if not wavelet:
            logging.error("cant get wavelet")
            return

        logging.warn('wave - out - %s - %s' % (self.data.title, txt))
        try:
            annotations = []
            for url in txt.split():
                if url.startswith("http://"):
                    logging.warn("wave - found url - %s" % str(url))
                    start = txt.find(url)
                    if start:
                        annotations.append((start+1, start+len(url), "link/manual", url))
        except Exception, ex:
            handle_exception()

        logging.warn("annotations used: %s", annotations)
        reply = wavelet.reply(txt)
        if annotations:
            for ann in annotations:
                if ann[0]:
                    try:
                        reply.range(ann[0], ann[1]).annotate(ann[2], ann[3])
                    except Exception, ex:
                        handle_exception()

        logging.warn("submitting to server: %s" % wavelet.serialize())
        try:
            bot.submit(wavelet)
        except google.appengine.api.urlfetch_errors.DownloadError:
            handle_exception()

        self.data.seenblips += 1
        self.data.lastedited = time.time()
        self.save()

    def toppost(self, bot, txt):
        """ toppost some txt to the wave. """
        if self.data.json_data:
            logging.debug("wave - say - using BLIND - %s" % self.data.json_data) 
            wavelet = bot.blind_wavelet(self.data.json_data)
        else:
            logging.info("did not join channel %s" % self.id)
            return
        if not wavelet:
            logging.error("cant get wavelet")
            return

        logging.warn('wave - out - %s - %s' % (self.data.title, txt))
        try:
            blip = wavelet._root_blip.reply()
            blip.append(txt)
            bot.submit(wavelet)
        except google.appengine.api.urlfetch_errors.DownloadError:
            handle_exception()

        self.data.seenblips += 1
        self.data.lastedited = time.time()
        self.save()
