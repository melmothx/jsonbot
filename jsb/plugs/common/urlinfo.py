# urlinfo.py
# -*- coding: utf-8 -*-

"""
Catches URLs on channel and gives information about them like title, image size, etc.
Uses http://whatisthisfile.appspot.com/ via XMLRPC

Example:
19:20 <@raspi> http://www.youtube.com/watch?v=9RZ-hYPAMFQ
19:20 <@bot> Title: "YouTube - Black Knight Holy Grail"
19:28 <@raspi> test http://www.raspi.fi foobar http://raspi.fi/wp-includes/images/rss.png
19:28 <@bot> 1. Title: "raspi.fi" Redirect: http://raspi.fi/  2. Image: 14x14
"""

__author__ = u"Pekka 'raspi' Järvinen - http://raspi.fi/"
__license__ = 'BSD'

from jsb.utils.exception import handle_exception
from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.lib.persist import PlugPersist
from jsb.lib.examples import examples


import re
import urlparse
import xmlrpclib
import socket
import logging

""" Gets information about URLs spoken on channel. """

cfg = PlugPersist('urlinfo', {})


# Remove non-urls word by word
def sanitize(text):
  text = text.strip()

  # Remove extra space
  text = re.sub('\s\s+', ' ', text)

  tmp = ''
  for i in text.split(' '):
    if len(i) >= 5:
      if i.find('www.') != -1 or i.find('http') != -1:
        # String has to contain www. or http somewhere
        tmp += i + ' '

  tmp = tmp.strip();
  
  tmp2 = ''
  for i in tmp.split(' '):
    if (i[0] == '(' and i[-1] == ')') or (i[0] == '[' and i[-1] == ']') or (i[0] == '<' and i[-1] == '>') or (i[0] == '{' and i[-1] == '}'):
      # First and last character is one of ()[]{}<>
      tmp2 += i[1:-1:1] + ' '
    else:
      tmp2 += i + ' '

  tmp2 = tmp2.strip();
  tmp = ''
  for i in tmp2.split(' '):
    if i.find('www.') == 0:
      # Add http:// to beginning of string
      tmp += 'http://' + i + ' '
    else:
      tmp += i + ' '

  tmp = tmp.strip();
  out = tmp;

  return out;

# Get valid URLs
def getUrls(text):
  regex = r"http[s]?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]"
  p = re.compile(regex)
  urls = []
  
  for i in text.split(' '):
    for x in p.findall(i):
      url = urlparse.urlparse(x)
      if url.geturl() not in urls:
        urls.append(url.geturl())
      
  return urls

# Get URL information
def getUrlInfo(text):
  out = ''
  text = sanitize(text)
  urls = getUrls(text)
  if urls:
    idx = 1
    for i in urls:
      o = ''
      try:
        #socket.setdefaulttimeout(30)

        server = xmlrpclib.ServerProxy("http://whatisthisfile.appspot.com/xmlrpc")
        logging.info('urlinfo - XMLRPC query: %s' % i)
        urlinfo = server.app.query(i)
        if urlinfo.has_key('html'):
          if urlinfo['html'].has_key('title'):
            o += 'Title: "%s" ' % urlinfo['html']['title'].strip()
        elif urlinfo.has_key('image'):
          o += 'Image: %dx%d ' % (urlinfo['image']['width'], urlinfo['image']['height'])

        if urlinfo.has_key('real_url'):
          if urlinfo['real_url'] != i:
            o += 'Redirect: %s ' % (urlinfo['real_url'])

        if len(o):
          if len(urls) > 1:
            out += ' ' + str(idx) + '. '
            idx += 1

          out += o

      except Exception:
        pass
  return out.strip()

# Catch channel chat for possible URLs
def catchHasUrls(bot, ievent):
  if ievent.how == "background":
    return 0
  if cfg.data.has_key(ievent.channel) and cfg.data[ievent.channel]:
    if len(ievent.txt) >= 5:
      if (ievent.txt.find('www.') != -1) or (ievent.txt.find('http') != -1):
        return 1
  return 0  

# Catch channel chat
def catchUrls(bot, ievent):
  bot.say(ievent.channel, getUrlInfo(ievent.txt))

callbacks.add('PRIVMSG', catchUrls, catchHasUrls, threaded=True)
callbacks.add('CONSOLE', catchUrls, catchHasUrls, threaded=True)
callbacks.add('MESSAGE', catchUrls, catchHasUrls, threaded=True)
callbacks.add('DISPATCH', catchUrls, catchHasUrls, threaded=True)

# Enable on channel
def handle_urlinfo_enable(bot, ievent):
  cfg.data[ievent.channel] = True
  cfg.save()
  ievent.reply('urlinfo enabled')

cmnds.add('urlinfo-enable', handle_urlinfo_enable, ['OPER'])
examples.add('urlinfo-enable', 'enable urlinfo in the channel', 'urlinfo-enable')

# Disable on channel
def handle_urlinfo_disable(bot, ievent):
   cfg.data[ievent.channel] = False
   cfg.save()
   ievent.reply('urlinfo disabled')

cmnds.add('urlinfo-disable', handle_urlinfo_disable, 'OPER')
examples.add('urlinfo-disable', 'disable urlinfo in the channel', 'urlinfo-disable')

def handle_urlinfo_list(bot, ievent):
  chans = []
  names = cfg.data.keys()
  names.sort()
  
  for name in names:
    targets = cfg.data.keys()
    targets.sort()
    chans.append('%s: %s' % (name, ' '.join(targets)))
  if not chans:
    ievent.reply('none')
  else:
    ievent.reply('urlinfo enabled on channels: %s' % ', '.join(chans))

cmnds.add('urlinfo-list', handle_urlinfo_list, 'OPER')
examples.add('urlinfo-list', 'show in which channels urlinfo is enabled', 'urlinfo-list')
