# commonplugs/rss.py
#
#

"""
    the rss mantra is of the following:

        1) add a url with rss-add <feedname> <url>
        2) use rss-start <feed> 

"""

## gozerlib imports

from gozerlib.persist import Persist, PlugPersist
from gozerlib.utils.url import geturl2, striphtml, useragent
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.generic import strippedtxt, fromenc, toenc, jsonstring, getwho
from gozerlib.utils.rsslist import rsslist
from gozerlib.utils.lazydict import LazyDict
from gozerlib.utils.statdict import StatDict
from gozerlib.utils.timeutils import strtotime
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.dol import Dol
from gozerlib.utils.pdod import Pdod
from gozerlib.utils.pdol import Pdol
from gozerlib.users import users
from gozerlib.utils.id import getrssid
from gozerlib.tasks import taskmanager
from gozerlib.callbacks import callbacks
from gozerlib.fleet import getfleet
from gozerlib.threadloop import TimedLoop
from gozerlib.threads import start_new_thread
from gozerlib.errors import NoSuchBotType, FeedAlreadyExists, NameNotSet
from gozerlib.datadir import getdatadir

import gozerlib.contrib.feedparser as feedparser

## google imports

try:
    from google.appengine.api.memcache import get, set, delete
except ImportError:
    from gozerlib.cache import get, set, delete

## tinyurl import

try:
    from commonplugs.tinyurl import get_tinyurl
except ImportError:
    def get_tinyurl(url):
        return [url, ]

## simplejson import

from simplejson import loads

## basic imports

import time
import os
import types
import thread
import socket
import xml
import logging
import datetime
import hashlib

## define

allowedtokens = ['updated', 'link', 'summary', 'tags', 'author', 'content', 'title', 'subtitle']
savelist = []
possiblemarkup = {'separator': 'set this to desired item separator', \
'all-lines': "set this to 1 if you don't want items to be aggregated", \
'tinyurl': "set this to 1 when you want to use tinyurls", 'skipmerge': \
"set this to 1 if you want to skip merge commits", 'reverse-order': \
'set this to 1 if you want the rss items displayed with oldest item first', \
'nofeedname': "if you don't want the feedname shown"}

def txtindicts(result, d):
    """ return lowlevel values in (nested) dicts. """
    for j in d.values():
        if type(j) == types.DictType: txtindicts(result, j) 
        else: result.append(j)

def checkfordate(data, date):
    """ see if date is in data (list of feed items). """
    if not data: return False
    for item in data:
        try: d = item['updated']
        except (KeyError, TypeError): continue
        if date == d: return True
    return False

def find_self_url(links):
    for link in links:
        logging.debug("rss - trying link: %s" % (link))
        if link.rel == 'self': return link.href
    return None

## exceptions

class RssException(Exception):
    pass

class Rss301(RssException):
    pass

class RssStatus(RssException):
    pass

class RssBozoException(RssException):
    pass

class RssNoSuchItem(RssException):
    pass

## defines

lastpoll = PlugPersist('lastpoll')
if not lastpoll.data: lastpoll.data = LazyDict() ; lastpoll.save()

sleeptime = PlugPersist('sleeptime')
if not sleeptime.data: sleeptime.data = LazyDict() ; sleeptime.save()

runners = PlugPersist('runners')
if not runners.data: runners.data = LazyDict() ; runners.save()

## Feed class

class Feed(Persist):

    """ item that contains rss data """

    def __init__(self, name="nonameset", url="", owner="noownerset", itemslist=['title', 'link'], watchchannels=[], \
sleeptime=15*60, running=0):
        if name:
            filebase = getdatadir() + os.sep + 'plugs' + os.sep + 'commonplugs.rss' + os.sep + name
            Persist.__init__(self, filebase + '-core')
            if not self.data: self.data = {}
            self.data = LazyDict(self.data)
            self.data['name'] = self.data.name or unicode(name)
            self.data['url'] = self.data.url or unicode(url)
            self.data['owner'] = self.data.owner or unicode(owner)
            self.data['result'] = []
            self.data['seen'] = self.data.seen or []
            self.data['watchchannels'] = self.data.watchchannels or list(watchchannels)
            self.data['running'] = self.data.running or running
            self.itemslists = Pdol(filebase + '-itemslists')
            self.markup = Pdod(filebase + '-markup')
        else: raise NameNotSet()

    def checkseen(self, data):
        digest = hashlib.md5(unicode(data)).hexdigest()
        return digest in self.data.seen

    def setseen(self, data):
        digest = hashlib.md5(unicode(data)).hexdigest()
        self.data.seen.insert(0, digest)
        if len(self.data.seen) > 100: self.data.seen = self.data.seen[:100]
        return self.data.seen

    def ownercheck(self, userhost):
        """ check is userhost is the owner of the feed. """
        try: return self.data.owner.lower() == userhost.lower()
        except KeyError: pass
        return False

    def save(self, coreonly=False):
        """ save rss data. """
        Persist.save(self)
        if not coreonly:
            self.itemslists.save()
            self.markup.save()

    def getdata(self):
        """ return data from cache or run fetchdata() to retrieve them. """
        url = self.data['url']
        result = get(url, namespace='rss')
        if result == None:
            result = self.fetchdata()
            set(url, result, namespace='rss')
            logging.debug("rss - got result from %s" % url)
        else: logging.debug("rss - got result from %s *cached*" % url)
        return result

    def fetchdata(self, data=None):
        """ get data of rss feed. """

        name = self.data.name
        global etags
        if name and etags.data.has_key(name): etag = etags.data[name]
        else: etag = None
        if data:
            result = feedparser.parse(data.content, etag=etag)
            try: status = data.status_code
            except AttributeError: status = None
        else:
            url = self.data['url']
            logging.debug("rss - fetching %s" % url)
            result = feedparser.parse(url, agent=useragent(), etag=etag)
            try: status = result.status
            except AttributeError: status = None
        logging.info("rss - status returned of %s feed is %s" % (name, status))
        if status == 301: return []
        if result: set(self.data.url, result, namespace='rss')
        if data:
            try: etag = etags.data[name] = data.headers.get('etag') ; logging.info("rss - etag of %s set to %s" % (name, etags.data[name])) ; etags.sync()
            except KeyError: etag = None
        else:
            try: etag = etags.data[name] = result.etag ; logging.info("rss - etag of %s set to %s" % (name, etags.data[name])) ; etags.sync()
            except KeyError: etag = None
        logging.info("rss - etag of %s feed is %s" % (name, etag))
        if not name in urls.data: urls.data[name] = self.data.url ; urls.save()
        logging.debug("rss - got result from %s" % self.data.url)
        if result and result.has_key('bozo_exception'): logging.warn('rss - %s bozo_exception: %s' % (url, result['bozo_exception']))
        try:
            status = result.status
            logging.info("rss - status is %s" % status)
        except AttributeError: status = 200
        return result.entries

    def sync(self):
        """ refresh cached data of a feed. """
        if not self.data.running:
            logging.info("rss - %s not enabled .. %s not syncing " % (self.data.name, self.data.url))
            return False
        logging.info("rss - syncing %s - %s" % (self.data.name, self.data.url))
        result = self.fetchdata()
        if not result:
            cached = get(self.data.url, namespace="rss")
            if cached: result = cached.entries
            else: result = []
        return result

    def check(self, entries=None, save=True):
        got = False
        tobereturned = []
        if entries == None: entries = self.fetchdata()
        if entries:
            for res in entries[::-1]:
                if self.checkseen(res): continue 
                #dt = feedparser._parse_date(res.updated)
                #dtt = time.mktime(dt)
                tobereturned.append(LazyDict(res))
                got = True
                self.setseen(res)
            if got and save: self.save()
            logging.debug("rss - %s - got %s rss items" % (self.data.name, len(tobereturned)))
        return tobereturned

    def deliver(self, datalist, save=True):
        name = self.data.name
        try:
            loopover = self.data.watchchannels
            logging.debug("loopover in %s deliver is: %s" % (self.data.name, loopover))
            for item in loopover:
                if not item: continue
                try:
                    (botname, type, channel) = item
                except ValueError:
                    logging.debug('rss - %s is not in the format (botname, type, channel)' % str(item))
                    continue
                if not botname: logging.error("rss - %s - %s is not correct" % (name, str(item))) ; continue
                if not type: logging.error("rss - %s - %s is not correct" % (name, str(item))) ; continue
                try:
                    bot = getfleet().byname(botname)
                    if not bot: bot = getfleet().makebot(type, botname)
                except NoSuchBotType, ex: logging.warn("rss - can't make bot - %s" % str(ex)) ; continue
                if not bot: logging.error("rss - can't find %s bot in fleet" % botname) ; continue
                res2 = datalist
                if type == "irc" and not '#' in channel: nick = getwho(bot, channel)
                else: nick = None                        
                if self.markup.get(jsonstring([name, type, channel]), 'reverse-order'): res2 = res2[::-1]
                if self.markup.get(jsonstring([name, type, channel]), 'all-lines'):
                    for i in res2: 
                        response = self.makeresponse(name, type, [i, ], channel)
                        try: bot.say(nick or channel, response)
                        except Exception, ex: handle_exception()
                else:
                    sep =  self.markup.get(jsonstring([name, type, channel]), 'separator')
                    if sep: response = self.makeresponse(name, type, res2, channel, sep=sep)
                    else: response = self.makeresponse(name, type, res2, channel)
                    try: bot.say(nick or channel, response)
                    except Exception, ex: handle_exception()
            return True
        except Exception, ex: handle_exception(txt=name) ; return False

    def makeresponse(self, name, type, res, channel, sep=" .. "):
        """ loop over result to make a response. """
        if self.markup.get(jsonstring([name, type, channel]), 'nofeedname'): result = u""
        else: result = u"<b>[%s]</b> - " % name 
        try: itemslist = self.itemslists.data[jsonstring([name, type, channel])]
        except KeyError:
            itemslist = self.itemslists.data[jsonstring([name, type, channel])] = ['title', 'link']
            self.itemslists.save()
        for j in res:
            if self.markup.get(jsonstring([name, type, channel]), 'skipmerge') and 'Merge branch' in j['title']: continue
            resultstr = u""
            for i in itemslist:
                try:
                    item = getattr(j, i)
                    if not item: continue
                    item = unicode(item)
                    if item.startswith('http://'):
                        if self.markup.get(jsonstring([name, type, channel]), 'tinyurl'):
                            try:
                                tinyurl = get_tinyurl(item)
                                logging.debug('rss - tinyurl is: %s' % str(tinyurl))
                                if not tinyurl: resultstr += u"%s - " % item
                                else: resultstr += u"%s - " % tinyurl[0]
                            except Exception, ex:
                                handle_exception()
                                resultstr += u"%s - " % item
                        else: resultstr += u"%s - " % item
                    else: resultstr += u"%s - " % item.strip()
                except (KeyError, AttributeError, TypeError), ex: logging.warn('rss - %s - %s' % (name, str(ex))) ; continue
            resultstr = resultstr[:-3]
            if resultstr: result += u"%s %s " % (resultstr, sep)
        return result[:-(len(sep)+2)]

    def all(self):
        """ get all entries of the feed. """
        return self.getdata()

    def search(self, item, search):
        """ search feed entries. """
        res = []
        for result in self.all():
            try: i = getattr(result, item)
            except AttributeError: continue
            if i and search in i: res.append(i)
        return res


class Rssdict(PlugPersist):

    """ dict of rss entries """

    def __init__(self, filename, feedname=None):
        self.sleepsec = 900
        self.feeds = LazyDict()
        PlugPersist.__init__(self, filename)
        if not self.data:
            self.data = LazyDict()
            self.data['names'] = []
            self.data['urls'] = {}
        else:
            self.data = LazyDict(self.data)
            if not self.data.has_key('names'): self.data['names'] = []
            if not self.data.has_key('urls'): self.data['urls'] = {}
            if not feedname: pass
            else: self.feeds[feedname] = Feed(feedname)
        #self.startwatchers()

    def save(self, namein=None):
        """ save all feeds or provide a feedname to save. """
        PlugPersist.save(self)
        for name, feed in self.feeds.iteritems():
            if namein and name != namein: continue
            try: feed.save()
            except Exception, ex: handle_exception()

    def size(self):
        """ return number of rss feeds. """
        return len(self.data['names'])

    def add(self, name, url, owner):
        """ add rss item. """
        logging.warn('rss - adding %s - %s - (%s)' % (name, url, owner))
        if name not in self.data['names']: self.data['names'].append(name)
        else: raise FeedAlreadyExists("feed already exists: %s" % name)
        self.feeds[name] = Feed(name, url, owner, ['title', 'link'])
        self.data['urls'][url] = name
        self.feeds[name].save()
        self.watch(name)
        self.save(name)

    def delete(self, name):
        """ delete rss item by name. """
        target = self.byname(name)
        if target:
            target.data.stoprunning = 1
            target.data.running = 0
            target.save()
            try: del self.feeds[name]
            except KeyError: pass
            try: self.data['names'].remove(name)
            except ValueError: pass
            self.save()

    def byname(self, name):
        """ return rss item by name. """
        if not name: return
        item = Feed(name)
        if item.data.url: return item 

    def cloneurl(self, url, auth):
        """ add feeds from remote url. """
        data = geturl2(url)
        got = []
        for line in data.split('\n'):
            try: (name, url) = line.split()
            except ValueError: logging.debug("rss - cloneurl - can't split %s line" % line) ; continue
            if self.byname(name): logging.debug('rss - cloneurl - already got %s feed' % name) ; continue
            if url.endswith('<br>'): url = url[:-4]
            self.add(name, url, auth)
            got.append(name)
        return got

    def getdata(self, name):
        """ get data of rss feed. """
        rssitem = self.byname(name)
        if rssitem == None: raise RssNoSuchItem("no %s rss item found" % name)
        return rssitem.getdata()

    def watch(self, name, sleepsec=900):
        """ start a watcher thread """
        logging.debug('trying %s rss feed watcher' % name)
        rssitem = self.byname(name)
        if rssitem == None: raise RssNoItem()
        if not rssitem.data.running:
            rssitem.data.running = 1
            rssitem.data.stoprunning = 0
            rssitem.check(rssitem.sync())
            rssitem.save()
        runners.data[name] = "bla"
        runners.save()
        #lastpoll.data[name] = time.time()
        #lastpoll.save()
        sleeptime.data[name] = sleepsec
        sleeptime.save()
        logging.info('rss - started %s rss watch' % name)

class Rsswatcher(Rssdict):

    """ rss watchers. """ 

    def checkfeed(self, url, event):
        """ get data of rss feed. """
        result = feedparser.parse(url, agent=useragent())
        logging.info("rss - fetch - got result from %s" % url)
        if result and result.has_key('bozo_exception'):
            event.reply('rss - %s bozo_exception: %s' % (url, result['bozo_exception']))
            return False
        try: status = result.status ; event.reply("rss - %s - status is %s" % (url, status))
        except AttributeError: status = 200
        if status != 200 and status != 301 and status != 302: return False
        return True

    def byurl(self, url):
        try: name = self.data['urls'][url]
        except KeyError: return
        return self.byname(name)

    def handle_data(self, data, name=None):
        """ handle data received in callback. """
        try:
            if name: rssitem = self.byname(name)
            else: url = find_self_url(result.feed.links) ; rssitem = self.byurl(url)
            if rssitem: name = rssitem.data.name
            else: logging.warn("rss - can't find %s item" % url) ; del data ; return
            if not name in urls.data: urls.data[name] = url ; urls.save()
            result = rssitem.fetchdata(data)
            logging.warn("rss - %s - got %s items" % (name, len(result)))
            res = rssitem.check(result)
            if res: rssitem.deliver(res, save=True)
            else: logging.warn("rss - %s - no items to deliver" % name)
        except Exception, ex: handle_exception(txt=name)
        del data
        return True

    def insertdata(self, data):
        """ get data of rss feed. """  
        result = feedparser.parse(data)
        url = find_self_url(result.feed.links)  
        logging.debug("rss - insert - %s" % url)
        try:
            rssitem = self.byurl(url)
            if rssitem: loopover = rssitem.data.watchchannels ; name = rssitem.data.name
            else: logging.debug("rss - can't find %s item" % url) ; return
            logging.debug("loopover in %s is: %s" % (rssitem.data.name, loopover))
            for item in loopover:
                try: (botname, type, channel) = item
                except: logging.debug('rss - %s is not in the format (botname,channel)' % str(item))
                bot = getfleet().byname(botname)
                if not bot: logging.debug("rss - can't find %s bot in fleet" % botname) ; continue
                res2 = result.entries
                if not res2:
                    logging.debug("rss - no updates for %s (%s) feed available" % (rssitem.data.name, channel))
                    continue
                if type == "irc" and not '#' in channel: nick = getwho(bot, channel)
                else: nick = None                        
                if rssitem.markup.get(jsonstring([name, type, channel]), 'reverse-order'): res2 = res2[::-1]
                if rssitem.markup.get(jsonstring([name, type, channel]), 'all-lines'):
                    for i in res2:
                        response = self.makeresponse(name, type, [i, ], channel)
                        try: bot.say(nick or channel, response) 
                        except Exception, ex: handle_exception()
                else:
                    sep =  rssitem.markup.get(jsonstring([name, type, channel]), 'separator')
                    if sep: response = self.makeresponse(name, type, res2, channel, sep=sep)
                    else: response = self.makeresponse(name, type, res2, channel)
                    try: bot.say(nick or channel, response) 
                    except Exception, ex: handle_exception()
        except Exception, ex: handle_exception(txt=name)
        return True

    def getall(self):
        """ get all feeds. """
        for name in self.data['names']: self.feeds[name] = Feed(name)
        return self.feeds
       
    def shouldpoll(self, name, curtime):
        """ check whether poll of feed in needed. """
        return self.byname(name).shouldpoll(curtime)

    def get(self, name, userhost, save=True):
        """ get entries for a user. """
        return self.byname(name).get(userhost, save)

    def check(self, name, entries=None, save=True):
        """ check for updates. """
        return self.byname(name).check(entries=entries, save=save)

    def sync(self, name):
        """ sync a feed. """
        feed = self.byname(name)
        if feed:
            result = feed.sync()
            if result:
                res2 = self.check(name, result)
                if res2: feed.deliver(res2)

    def ownercheck(self, name, userhost):
        """ check if userhost is the owner of feed. """
        try:
            feed = self.byname(name)
            if feed: return feed.ownercheck(userhost)
        except KeyError: pass
        return False

    def changeinterval(self, name, interval):
        """ not implemented yet. """
        sleeptime.data[name] = interval
        sleeptime.save()

    def stopwatchers(self):
        """ stop all watcher threads. """
        for j, z in self.data.iteritems():
            if z.data.running: z.data.stoprunning = 1

    def dowatch(self, name, sleeptime=1800):
        """ start a watcher. """
        rssitem = self.byname(name)
        if not rssitem == None:
            logging.error("rss - no %s rss item available" % name)
            return
        while 1:
            try: self.watch(name)
            except Exception, ex:
                logging.warn('rss - %s feed error: %s' % (name, str(ex)))
                if not rssitem.data.running: break
            else: break

    def makeresult(self, name, type, target, data):
        """ make a result (txt) of a feed depending on its itemlist. """
        rssitem = self.byname(name)
        if not rssitem == None: logging.error("rss - no %s rss item available" % name) ; return
        res = []
        for j in data:
            tmp = {}
            if not rssitem.itemslists.data[jsonstring([name, type, target])]: return []
            for i in rssitem.itemslists.data[jsonstring([name, type, target])]:
                try: tmp[i] = unicode(j[i])
                except KeyError: continue
            res.append(tmp)
        return res


    def makeresponse(self, name, type, res, channel, sep=" .. "):
        """ loop over result to make a response. """
        rssitem = self.byname(name)
        if not rssitem: logging.error("rss - no %s rss item available" % name) ; return
        if rssitem.markup.get(jsonstring([name, type, channel]), 'nofeedname'): result = u""
        else: result = u"<b>[%s]</b> - " % name 
        try: itemslist = rssitem.itemslists.data[jsonstring([name, type, channel])]
        except KeyError:
            itemslist = rssitem.itemslists.data[jsonstring([name, type, channel])] = ['title', 'link']
            rssitem.itemslists.save()
        for j in res:
            if rssitem.markup.get(jsonstring([name, type, channel]), 'skipmerge') and 'Merge branch' in j['title']: continue
            resultstr = u""
            for i in itemslist:
                try:
                    item = getattr(j, i)
                    if not item: continue
                    item = unicode(item)
                    if item.startswith('http://'):
                        if rssitem.markup.get(jsonstring([name, type, channel]), 'tinyurl'):
                            try:
                                tinyurl = get_tinyurl(item)
                                logging.debug('rss - tinyurl is: %s' % str(tinyurl))
                                if not tinyurl: resultstr += u"%s - " % item
                                else: resultstr += u"%s - " % tinyurl[0]
                            except Exception, ex:
                                handle_exception()
                                resultstr += u"%s - " % item
                        else: resultstr += u"%s - " % item
                    else: resultstr += u"%s - " % item.strip()
                except (KeyError, AttributeError, TypeError), ex: logging.warn('rss - %s - %s' % (name, str(ex))) ; continue
            resultstr = resultstr[:-3]
            if resultstr: result += u"%s %s " % (resultstr, sep)
        return result[:-(len(sep)+2)]

    def stopwatch(self, name, save=True):
        """ stop watcher thread. """
        try:
            feed = self.byname(name)
            if feed:
                feed.data.running = 0
                feed.data.stoprunning = 1
                if save: feed.save()
        except KeyError: pass
        try:
             del runners.data[name]
             if save: runners.save()
             return True
        except KeyError: pass
        return False

    def list(self):
        """ return of rss names. """
        feeds = self.data['names']
        return feeds

    def runners(self):
        if runners.data: return runners.data.keys()
        return []

    def checkrunners(self):	
        """ show names/channels of running watchers. """
        result = []
        for name in self.data['names']:
            z = self.byname(name)
            if z and z.data.running == 1 and not z.data.stoprunning: 
                result.append((z.data.name, z.data.watchchannels))
                runners.data[name] = z.data.watchchannels
        runners.save()
        return result

    def getfeeds(self, botname, type, channel):
        """ show names/channels of running watcher. """
        result = []
        for name in self.runners():
            z = self.byname(name)
            if not z or not z.data.running: continue
            if jsonstring([botname, type, channel]) in z.data.watchchannels or [botname, type, channel] in z.data.watchchannels:
                result.append(z.data.name)
        return result

    def url(self, name):
        """ return url of rssitem. """
        return self.byname(name).data.url

    def seturl(self, name, url):
        """ set url of rssitem. """
        feed = self.byname(name)
        feed.data.url = url
        feed.save()
        return True

    def scan(self, name):
        """ scan a rss url for tokens. """
        #try: result = self.getdata(name)
        #except RssException, ex: logging.error('rss - scan - %s error: %s' % (name, str(ex))) ; return
        #if not result: return
        keys = []
        items = self.byname(name).getdata()
        for item in items:
            for key in item:
                if key in allowedtokens: keys.append(key)            
        statdict = StatDict()
        for key in keys: statdict.upitem(key)
        return statdict.top()  

    def search(self, name, item, search):
        """ search titles of a feeds cached data. """
        i = self.byname(name)
        if i: return i.search(item, search)
        return []

    def searchall(self, item, search):
        """ search titles of all cached data. """
        res = []
        for name in self.data['names']:
            feed = self.byname(name)
            res.append(str(feed.search(item, search)))
        return res

    def all(self, name, item):
        """ search all cached data of a feed. """
        res = []
        feed = self.byname(name)
        if not feed: return res
        for result in feed.all():
            try: txt = getattr(result, item)
            except AttributeError: continue
            if txt: res.append(txt)
        return res

    def startwatchers(self):
        """ start watcher threads """
        for name in self.data['names']:
            z = self.byname(name)
            if z and z.data.running: self.watch(z.data.name)

    def start(self, botname, bottype, name, channel):
        """ start a rss feed (per user/channel). """
        rssitem = self.byname(name)
        if rssitem == None: logging.warn("rss - we don't have a %s rss object" % name) ; return False
        target = channel
        if not jsonstring([botname, bottype, target]) in rssitem.data.watchchannels and not [botname, bottype, target] in rssitem.data.watchchannels:
            rssitem.data.watchchannels.append([botname, bottype, target])
        rssitem.itemslists[jsonstring([name, bottype, target])] = ['title', 'link']
        rssitem.markup.set(jsonstring([name, bottype, target]), 'tinyurl', 1)
        rssitem.data.running = 1
        rssitem.data.stoprunning = 0
        rssitem.save()
        watcher.watch(name)
        logging.warn("rss - started %s feed in %s channel" % (name, channel))
        return True

    def stop(self, botname, bottype, name, channel):
        """ stop a rss feed (per user/channel). """
        rssitem = self.byname(name)
        if not rssitem: return False
        try:
            rssitem.data.watchchannels.remove([botname, bottype, channel])
            rssitem.save()
            logging.warn("rss - stopped %s feed in %s channel" % (name, channel))
        except ValueError: return False
        return True

    def clone(self, botname, bottype, newchannel, oldchannel):
        """ clone feeds from one channel to another. """
        feeds = self.getfeeds(botname, oldchannel)
        for feed in feeds:
            self.stop(botname, bottype, feed, oldchannel)
            self.start(botname, bottype, feed, newchannel)
        return feeds

# the watcher object 

watcher = Rsswatcher('rss')
urls = PlugPersist('urls')
etags = PlugPersist('etags')

assert(watcher)

## dosync function
def dummycb(bot, event): pass

callbacks.add('START', dummycb)


def dosync(feedname):
    """ main level function to be deferred by periodical. """
    try:
       logging.info("rss - doing sync of %s" % feedname)
       localwatcher = Rsswatcher('rss', feedname)
       localwatcher.sync(feedname)
    except RssException, ex: logging.error("rss - %s - error: %s" % (feedname, str(ex)))

## shouldpoll function

def shouldpoll(name, curtime):
    """ check whether a new poll is needed. """
    global lastpoll
    try: lp = lastpoll.data[name]
    except KeyError: lp = lastpoll.data[name] = time.time() ; lastpoll.sync()
    global sleeptime
    try: st = sleeptime.data[name]
    except KeyError: st = sleeptime.data[name] = 900 ; sleeptime.sync()
    logging.debug("rss - pollcheck - %s - %s - remaining %s" % (name, time.ctime(lp), (lp + st) - curtime))
    if curtime - lp > st: return True

def dodata(data, name):
    watcher.handle_data(data, name=name)    

def rssfetchcb(rpc):
    import google
    try: data = rpc.get_result()
    except google.appengine.api.urlfetch_errors.DownloadError, ex: logging.warn("rss - %s - error: %s" % (rpc.final_url, str(ex))) ; return
    name = rpc.feedname
    logging.debug("rss - headers of %s: %s" % (name, unicode(data.headers)))
    if data.status_code == 200:
        logging.info("rss - defered %s feed" % rpc.feedname)
        from google.appengine.ext.deferred import defer
        defer(dodata, data, rpc.feedname)
    else: logging.warn("rss - fetch returned status code %s - %s" % (data.status_code, rpc.feedurl))

def create_rsscallback(rpc):
    return lambda: rssfetchcb(rpc)

## doperiodical function

def doperiodicalGAE(*args, **kwargs):
    """ rss periodical function. """
    from google.appengine.api import urlfetch
    curtime = time.time()
    feedstofetch = []
    rpcs = []
    for feed in watcher.runners():
        if not shouldpoll(feed, curtime): continue
        feedstofetch.append(feed)
    logging.info("rss - feeds to fetch: %s" % str(feedstofetch))
    got = False
    for f in feedstofetch:
        if not f: continue
        lastpoll.data[f] = curtime
        if f not in urls.data: url = Feed(f).data.url ; urls.data[f] = url ; got = True
        else: url = urls.data[f]
        rpc = urlfetch.create_rpc()
        rpc.feedname = f
        rpc.callback = create_rsscallback(rpc)
        rpc.feedurl = url
        try: etag = etags.data[f]
        except KeyError: etag = ""
        logging.info("rss - %s - sending request - %s" % (f, etag))
        try: urlfetch.make_fetch_call(rpc, url, headers={"If-None-Match": etag}) ; rpcs.append(rpc)
        except Exception, ex: handle_exception()
    for rpc in rpcs: 
        try: rpc.wait()
        except Exception, ex: handle_exception()
    if feedstofetch: lastpoll.save()
    if got: urls.save()

def doperiodical(*args, **kwargs):
    """ rss periodical function. """
    curtime = time.time()
    for feed in watcher.data.names:
        if not shouldpoll(feed, curtime): continue
        lastpoll.data[feed] = curtime
        lastpoll.save()
        logging.debug("rss - periodical - launching %s" % feed)
        try:
            from google.appengine.ext.deferred import defer
            defer(dosync, feed)
        except ImportError:
            try: start_new_thread(dosync, (feed, ))
            except Exception, ex: handle_exception() ; return

callbacks.add('TICK', doperiodical)

## init function

def init():
    taskmanager.add('rss', doperiodicalGAE)
    if not runners.data: watcher.checkrunners()
    
## shutdown function

def shutdown():
    taskmanager.unload('rss')

## size function

def size():
    """ return number of watched rss entries. """
    return watcher.size()

## save function

def save():
    """ save watcher data. """
    watcher.save()

## rss-clone command

def handle_rssclone(bot, event):
    """ clone feed running in a channel. """
    if not event.rest: event.missing('<channel>') ; event.done()
    feeds = watcher.clone(bot.name, event.channel, event.rest)
    event.reply('cloned the following feeds: ', feeds)
    bot.say(event.rest, "this wave is continued in %s" % event.url)
 
cmnds.add('rss-clone', handle_rssclone, 'USER')
examples.add('rss-clone', 'clone feeds into new channel', 'wave-clone waveid')

## rss-cloneurl command

def handle_rsscloneurl(bot, event):
    """ clone feeds from another bot (pointed to by url). """
    if not event.rest: event.missing('<url>') ; event.done
    feeds = watcher.cloneurl(event.rest, event.auth)
    event.reply('cloned the following feeds: ', feeds)
 
cmnds.add('rss-cloneurl', handle_rsscloneurl, 'OPER')
examples.add('rss-cloneurl', 'clone feeds from remote url', 'wave-clone jsonbot-hg http://jsonbot.appspot.com')

## rss-add command

def handle_rssadd(bot, ievent):
    """ rss-add <name> <url> .. add a rss item. """
    try: (name, url) = ievent.args
    except ValueError: ievent.missing('<name> <url>') ; return
    if watcher.byname(name):
        ievent.reply('we already have a feed with %s name .. plz choose a different name' % name)
        return
    if watcher.checkfeed(url, ievent): watcher.add(name, url, ievent.userhost) ; ievent.reply('rss item added')
    else: ievent.reply('%s is not valid' % url)

cmnds.add('rss-add', handle_rssadd, 'USER')
examples.add('rss-add', 'rss-add <name> <url> to the rsswatcher', 'rss-add jsonbot http://code.google.com/feeds/p/jsonbot/hgchanges/basic')

## rss-register command

def handle_rssregister(bot, ievent):
    """ rss-register <name> <url> .. register and start a rss item. """
    try: (name, url) = ievent.args
    except ValueError: ievent.missing('<name> <url>') ; return
    if watcher.byname(name):
        ievent.reply('we already have a feed with %s name .. plz choose a different name' % name)
        return
    if watcher.checkfeed(url, ievent):
        watcher.add(name, url, ievent.userhost)
        watcher.start(bot.name, bot.type, name, ievent.channel)
        if name not in ievent.chan.data.feeds: ievent.chan.data.feeds.append(name) ; ievent.chan.save()
        ievent.reply('rss item added and started in channel %s' % ievent.channel)
    else: ievent.reply('%s is not valid' % url)

cmnds.add('rss-register', handle_rssregister, 'USER')
examples.add('rss-register', 'rss-register <name> <url> - register and start a rss feed', 'rss-register jsonbot-hg http://code.google.com/feeds/p/jsonbot/hgchanges/basic')

## rss-del command

def handle_rssdel(bot, ievent):
    """ rss-del <name> .. delete a rss item. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    rssitem =  watcher.byname(name)
    if rssitem:
        if not watcher.ownercheck(name, ievent.userhost): ievent.reply("you are not the owner of the %s feed" % name) ; return
        watcher.stopwatch(name)
        watcher.delete(name)
        ievent.reply('rss item deleted')
    else: ievent.reply('there is no %s rss item' % name)

cmnds.add('rss-del', handle_rssdel, ['USER', ])
examples.add('rss-del', 'rss-del <name> .. remove <name> from the rsswatcher', 'rss-del mekker')

## rss-sync command

def handle_rsssync(bot, ievent):
    """ rss-del <name> .. delete a rss item. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    if name in watcher.data['names']: watcher.byname(name).sync() ; ievent.done()
    else: ievent.reply("no %s feed available" % name)

cmnds.add('rss-sync', handle_rsssync, ['USER', ])
examples.add('rss-sync', 'rss-sync <name> .. sync <name> feed', 'rss-sync mekker')

## rss-watch command

def handle_rsswatch(bot, ievent):
    """ rss-watch <name> .. start watcher thread. """
    if not ievent.channel: ievent.reply('no channel provided')
    try: name, sleepsec = ievent.args
    except ValueError:
        try: name = ievent.args[0] ; sleepsec = 1800
        except IndexError: ievent.missing('<name> [secondstosleep]') ; return
    try: sleepsec = int(sleepsec)
    except ValueError: ievent.reply("time to sleep needs to be in seconds") ; return
    if name == "all": target = watcher.data.names
    else: target = [name, ]
    got = []
    for feed in target:
        rssitem = watcher.byname(feed)
        if rssitem == None: continue
        if not rssitem.data.running or rssitem.data.stoprunning:
            if not sleeptime.data.has_key(name): sleeptime.data[feed] = sleepsec ; sleeptime.save()
            rssitem.data.running = 1
            rssitem.data.stoprunning = 0
            watcher.save(feed)
            try: watcher.watch(feed, sleepsec)
            except Exception, ex: ievent.reply('rss - %s - %s' % (feed, str(ex))) ; continue
            got.append(feed)
    if got: ievent.reply('watcher started ', got)
    else: ievent.reply('already watching ', target)


cmnds.add('rss-watch', handle_rsswatch, 'USER')
examples.add('rss-watch', 'rss-watch <name> [seconds to sleep] .. go watching <name>', '1) rss-watch jsonbot 2) rss-watch jsonbot 600')

## rss-start command

def handle_rssstart(bot, ievent):
    """ rss-start <name> .. start a rss feed to a user. """
    feeds = ievent.args
    if not feeds: ievent.missing('<list of feeds>') ; return
    started = []
    if feeds[0] == 'all': feeds = watcher.list()
    for name in feeds:
        watcher.start(bot.name, bot.type, name, ievent.channel)
        if name not in ievent.chan.data.feeds: ievent.chan.data.feeds.append(name) ; ievent.chan.save()
        started.append(name)
    ievent.reply('started: ', started)

cmnds.add('rss-start', handle_rssstart, ['RSS', 'USER'])
examples.add('rss-start', 'rss-start <name> .. start a rss feed \
(per user/channel) ', 'rss-start jsonbot')

## rss-stop command

def handle_rssstop(bot, ievent):
    """ rss-start <name> .. start a rss feed to a user. """
    if not ievent.rest: ievent.missing('<feed name>') ; return
    if ievent.rest == "all": loopover = ievent.chan.data.feeds
    else: loopover = [ievent.rest, ]
    stopped = []
    for name in loopover:
        if name in ievent.chan.data.feeds: ievent.chan.data.feeds.remove(name) 
        rssitem = watcher.byname(name)
        target = ievent.channel
        if rssitem == None: continue
        if not rssitem.data.running: continue
        try: rssitem.data.watchchannels.remove([bot.name, bot.type, target])
        except ValueError:
            try: rssitem.data.watchchannels.remove([bot.name, bot.type, target])
            except ValueError: continue
        rssitem.save()
        stopped.append(name)
    ievent.chan.save()
    ievent.reply('stopped feeds: ', stopped)

cmnds.add('rss-stop', handle_rssstop, ['RSS', 'USER'])
examples.add('rss-stop', 'rss-stop <name> .. stop a rss feed (per user/channel) ', 'rss-stop jsonbot')

## rss-stopall command

def handle_rssstopall(bot, ievent):
    """ rss-stop <name> .. stop all rss feeds to a channel. """
    if not ievent.rest: target = ievent.channel
    else: target = ievent.rest
    stopped = []
    feeds = watcher.getfeeds(bot.name, bot.type, target)
    if feeds:
        for feed in feeds:
            if watcher.stop(bot.name, bot.type, feed, target):
                if feed in ievent.chan.data.feeds: ievent.chan.data.feeds.remove(feed) ; ievent.chan.save()
                stopped.append(feed)
        ievent.reply('stopped feeds: ', stopped)
    else: ievent.reply('no feeds running in %s' % target)

cmnds.add('rss-stopall', handle_rssstopall, ['RSS', 'OPER'])
examples.add('rss-stopall', 'rss-stopall .. stop all rss feeds (per user/channel) ', 'rss-stopall')

## rss-channels command

def handle_rsschannels(bot, ievent):
    """ rss-channels <name> .. show channels of rss feed. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing("<name>")  ; return
    rssitem = watcher.byname(name)
    if rssitem == None: ievent.reply("we don't have a %s rss object" % name) ; return
    if not rssitem.data.watchchannels: ievent.reply('%s is not in watch mode' % name) ; return
    result = []
    for i in rssitem.data.watchchannels: result.append(str(i))
    ievent.reply("channels of %s: " % name, result)

cmnds.add('rss-channels', handle_rsschannels, ['OPER', ])
examples.add('rss-channels', 'rss-channels <name> .. show channels', 'rss-channels jsonbot')

## rss-addchannel command

def handle_rssaddchannel(bot, ievent):
    """ rss-addchannel <name> [<botname>] <channel> .. add a channel to rss item. """
    try: (name, botname, type, channel) = ievent.args
    except ValueError:
        try: (name, channel) = ievent.args ; botname = bot.name ; type = bot.type
        except ValueError:
            try: name = ievent.args[0] ; botname = bot.name ; type = bot.type ; channel = ievent.channel
            except IndexError: ievent.missing('<name> [<botname>] <channel>') ; return
    rssitem = watcher.byname(name)
    if rssitem == None: ievent.reply("we don't have a %s rss object" % name) ; return
    if not rssitem.data.running: ievent.reply('%s watcher is not running' % name) ; return
    if jsonstring([botname, type, channel]) in rssitem.data.watchchannels or [botname, channel] in rssitem.data.watchchannels:
        ievent.reply('we are already monitoring %s on (%s,%s)' % (name, botname, channel))
        return
    rssitem.data.watchchannels.append([botname, type, channel])
    rssitem.save()
    ievent.reply('%s added to %s rss item' % (channel, name))

cmnds.add('rss-addchannel', handle_rssaddchannel, ['OPER', ])
examples.add('rss-addchannel', 'add a channel to watchchannels of a feed', '1) rss-addchannel jsonbot #dunkbots 2) rss-addchannel jsonbot main #dunkbots')

## rss-setitems command

def handle_rsssetitems(bot, ievent):
    """ set items of a rss feed. """
    try: (name, items) = ievent.args[0], ievent.args[1:]
    except (ValueError, IndexError): ievent.missing('<name> <items>') ; return
    target = ievent.channel
    rssitem = watcher.byname(name)
    if not rssitem: ievent.reply("we don't have a %s feed" % name) ; return
    rssitem.itemslists.data[jsonstring([name, bot.type, target])] = items
    rssitem.itemslists.save()
    ievent.reply('%s added to (%s,%s) itemslist' % (items, name, target))

cmnds.add('rss-setitems', handle_rsssetitems, ['RSS', 'USER'])
examples.add('rss-setitems', 'set tokens of the itemslist (per user/channel)', 'rss-setitems jsonbot author author link pubDate')

## rss-additem command

def handle_rssadditem(bot, ievent):
    """ add an item (token) to a feeds itemslist. """
    try: (name, item) = ievent.args
    except ValueError: ievent.missing('<name> <item>') ; return
    target = ievent.channel
    feed = watcher.byname(name)
    if not feed: ievent.reply("we don't have a %s feed" % name) ; return
    try: feed.itemslists.data[jsonstring([name, bot.type, target])].append(item)
    except KeyError: feed.itemslists.data[jsonstring([name, bot.type, target])] = ['title', 'link']
    feed.itemslists.save()
    ievent.reply('%s added to (%s,%s) itemslist' % (item, name, target))

cmnds.add('rss-additem', handle_rssadditem, ['RSS', 'USER'])
examples.add('rss-additem', 'add a token to the itemslist (per user/channel)',\
 'rss-additem jsonbot link')

## rss-delitem command

def handle_rssdelitem(bot, ievent):
    """ delete item from a feeds itemlist. """
    try: (name, item) = ievent.args
    except ValueError: ievent.missing('<name> <item>') ; return
    target = ievent.channel
    rssitem =  watcher.byname(name)
    if not rssitem: ievent.reply("we don't have a %s feed" % name) ; return
    try:
        rssitem.itemslists.data[jsonstring([name, bot.type, target])].remove(item)
        rssitem.itemslists.save()
    except (ValueError, KeyError): ievent.reply("we don't have a %s rss feed" % name) ; return
    ievent.reply('%s removed from (%s,%s) itemslist' % (item, name, target))

cmnds.add('rss-delitem', handle_rssdelitem, ['RSS', 'USER'])
examples.add('rss-delitem', 'remove a token from the itemslist (per user/channel)', 'rss-delitem jsonbot link')

## rss-markuplist command

def handle_rssmarkuplist(bot, ievent):
    """ show possible markups that can be used. """
    ievent.reply('possible markups ==> ' , possiblemarkup)

cmnds.add('rss-markuplist', handle_rssmarkuplist, ['USER', ])
examples.add('rss-markuplist', 'show possible markup entries', 'rss-markuplist')

## rss-markup command

def handle_rssmarkup(bot, ievent):
    """ show the markup of a feed. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    rssitem =  watcher.byname(name)
    if not rssitem: ievent.reply("we don't have a %s feed" % name) ; return
    target = ievent.channel
    try: ievent.reply(str(rssitem.markup[jsonstring([name, bot.type, target])]))
    except KeyError: pass

cmnds.add('rss-markup', handle_rssmarkup, ['RSS', 'USER'])
examples.add('rss-markup', 'show markup list for a feed (per user/channel)', 'rss-markup jsonbot')

## rss-addmarkup command

def handle_rssaddmarkup(bot, ievent):
    """ add a markup to a feeds markuplist. """
    try: (name, item, value) = ievent.args
    except ValueError: ievent.missing('<name> <item> <value>') ; return
    rssitem =  watcher.byname(name)
    if not rssitem: ievent.reply("we don't have a %s feed" % name) ; return
    target = ievent.channel
    try: value = int(value)
    except ValueError: pass
    try:
        rssitem.markup.set(jsonstring([name, bot.type, target]), item, value)
        rssitem.markup.save()
        ievent.reply('%s added to (%s,%s) markuplist' % (item, name, target))
    except KeyError: ievent.reply("no (%s,%s) feed available" % (name, target))

cmnds.add('rss-addmarkup', handle_rssaddmarkup, ['RSS', 'USER'])
examples.add('rss-addmarkup', 'add a markup option to the markuplist (per user/channel)', 'rss-addmarkup jsonbot all-lines 1')

## rss-delmarkup command

def handle_rssdelmarkup(bot, ievent):
    """ delete markup from a feeds markuplist. """
    try: (name, item) = ievent.args
    except ValueError: ievent.missing('<name> <item>') ; return
    rssitem =  watcher.byname(name)
    if not rssitem: ievent.reply("we don't have a %s feed" % name) ; return
    target = ievent.channel
    try: del rssitem.markup[jsonstring([name, bot.type, target])][item]
    except (KeyError, TypeError): ievent.reply("can't remove %s from %s feed's markup" %  (item, name)) ; return
    rssitem.markup.save()
    ievent.reply('%s removed from (%s,%s) markuplist' % (item, name, target))

cmnds.add('rss-delmarkup', handle_rssdelmarkup, ['RSS', 'USER'])
examples.add('rss-delmarkup', 'remove a markup option from the markuplist (per user/channel)', 'rss-delmarkup jsonbot all-lines')

## rss-delchannel command

def handle_rssdelchannel(bot, ievent):
    """ delete channel from feed. """
    botname = None
    try: (name, botname, type, channel) = ievent.args
    except ValueError:
        try: (name, channel) = ievent.args ; type = bot.type ; botname = bot.name
        except ValueError:
            try:
                name = ievent.args[0]
                botname = bot.name
                type = bot.type
                channel = ievent.channel
            except IndexError: ievent.missing('<name> [<botname>] [<channel>]') ; return
    rssitem = watcher.byname(name)
    if rssitem == None: ievent.reply("we don't have a %s rss object" % name) ; return
    if jsonstring([botname, type, channel]) in rssitem.data.watchchannels:
        rssitem.data.watchchannels.remove(jsonstring([botname, type, channel]))
        ievent.reply('%s removed from %s rss item' % (channel, name))
    elif [botname, type, channel] in rssitem.data.watchchannels:
        rssitem.data.watchchannels.remove([botname, type, channel])
        ievent.reply('%s removed from %s rss item' % (channel, name))
    else: ievent.reply('we are not monitoring %s on (%s,%s)' % (name, botname, channel)) ; return
    rssitem.save()

cmnds.add('rss-delchannel', handle_rssdelchannel, ['OPER', ])
examples.add('rss-delchannel', 'delete channel from feed', '1) rss-delchannel jsonbot #dunkbots 2) rss-delchannel jsonbot main #dunkbots')

## rss-stopwatch command

def handle_rssstopwatch(bot, ievent):
    """ stop watching a feed. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    stopped = []
    if name == "all":
        for name in watcher.runners():
            if watcher.stopwatch(name): stopped.append(name)
    else:
        if watcher.stopwatch(name): stopped.append(name)
    ievent.reply('stopped rss watchers: ', stopped)

cmnds.add('rss-stopwatch', handle_rssstopwatch, ['OPER', ])
examples.add('rss-stopwatch', 'rss-stopwatch <name> .. stop polling <name>', 'rss-stopwatch jsonbot')

## rss-sleeptime command

def handle_rsssleeptime(bot, ievent):
    """ get sleeptime of rss item. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    try: ievent.reply('sleeptime for %s is %s seconds' % (name, str(sleeptime.data[name])))
    except KeyError: ievent.reply("can't get sleeptime for %s" % name)

cmnds.add('rss-sleeptime', handle_rsssleeptime, 'USER')
examples.add('rss-sleeptime', 'rss-sleeptime <name> .. get sleeping time \
for <name>', 'rss-sleeptime jsonbot')

## rss-setsleeptime command

def handle_rsssetsleeptime(bot, ievent):
    """ set sleeptime of feed. """
    try: (name, sec) = ievent.args ; sec = int(sec)
    except ValueError: ievent.missing('<name> <seconds>') ; return
    if not watcher.ownercheck(name, ievent.userhost): ievent.reply("you are not the owner of the %s feed" % name) ; return
    if sec < 60: ievent.reply('min is 60 seconds') ; return
    rssitem = watcher.byname(name)
    if rssitem == None: ievent.reply("we don't have a %s rss item" % name) ; return
    rssitem.data.sleeptime = sec
    if rssitem.data.running:
        try: watcher.changeinterval(name, sec)
        except KeyError, ex: ievent.reply("failed to set interval: %s" % str(ex)) ; return
    ievent.reply('sleeptime set')

cmnds.add('rss-setsleeptime', handle_rsssetsleeptime, ['USER', ])
examples.add('rss-setsleeptime', 'rss-setsleeptime <name> <seconds> .. set \
sleeping time for <name> .. min 60 sec', 'rss-setsleeptime jsonbot 600')

## rss-get command

def handle_rssget(bot, ievent):
    """ fetch feed data. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    channel = ievent.channel
    rssitem = watcher.byname(name)
    if rssitem == None: ievent.reply("we don't have a %s rss item" % name) ; return
    try: result = watcher.getdata(name)
    except Exception, ex: ievent.reply('%s error: %s' % (name, str(ex))) ; return
    if rssitem.markup.get(jsonstring([name, bot.type, channel]), 'reverse-order'): result = result[::-1]
    response = watcher.makeresponse(name, bot.type, result, ievent.channel)
    if response: ievent.reply("results of %s: %s" % (name, response))
    else: ievent.reply("can't make a reponse out of %s" % name)

cmnds.add('rss-get', handle_rssget, ['RSS', 'USER'], threaded=True)
examples.add('rss-get', 'rss-get <name> .. get data from <name>', 'rss-get jsonbot')

## rss-running command

def handle_rssrunning(bot, ievent):
    """ show which watchers are running. """
    result = watcher.runners()
    resultlist = []
    teller = 1
    for i in result: resultlist.append(i)
    if resultlist: ievent.reply("running rss watchers: ", resultlist)
    else: ievent.reply('nothing running yet')

cmnds.add('rss-running', handle_rssrunning, ['RSS', 'USER'])
examples.add('rss-running', 'rss-running .. get running rsswatchers', \
'rss-running')

## rss-list command

def handle_rsslist(bot, ievent):
    """ return list of rss items. """
    result = watcher.list()
    result.sort()
    if result: ievent.reply("rss items: ", result)
    else: ievent.reply('no rss items yet')

cmnds.add('rss-list', handle_rsslist, ['RSS', 'USER'])
examples.add('rss-list', 'get list of rss items', 'rss-list')

## rss-url command

def handle_rssurl(bot, ievent):
    """ return url of feed. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    if not watcher.ownercheck(name, ievent.userhost): ievent.reply("you are not the owner of the %s feed" % name) ; return
    result = watcher.url(name)
    if not result: ievent.reply("don't know url for %s" % name) ; return
    try:
        if ':' in result.split('/')[1]:
            if not ievent.msg: ievent.reply('run this command in a private message') ; return
    except (TypeError, ValueError, IndexError): pass
    ievent.reply('url of %s: %s' % (name, result))

cmnds.add('rss-url', handle_rssurl, ['OPER', ])
examples.add('rss-url', 'get url of feed', 'rss-url jsonbot')

## rss-seturl command

def handle_rssseturl(bot, ievent):
    """ set url of feed. """
    try: name = ievent.args[0] ; url = ievent.args[1]
    except IndexError: ievent.missing('<name> <url>') ; return
    if not watcher.ownercheck(name, ievent.userhost): ievent.reply("you are not the owner of the %s feed" % name) ; return
    oldurl = watcher.url(name)
    if not oldurl: ievent.reply("no %s rss item found" % name) ; return
    if watcher.seturl(name, url): watcher.sync(name) ; ievent.reply('url of %s changed' % name)
    else: ievent.reply('failed to set url of %s to %s' % (name, url))

cmnds.add('rss-seturl', handle_rssseturl, ['USER', ])
examples.add('rss-seturl', 'change url of rssitem', 'rss-seturl jsonbot-hg http://code.google.com/feeds/p/jsonbot/hgchanges/basic')

## rss-itemslist

def handle_rssitemslist(bot, ievent):
    """ rss-itemslist <name> .. show itemslist of rss item. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    rssitem = watcher.byname(name)
    if not rssitem: ievent.reply("we don't have a %s feed." % name) ; return
    try: itemslist = rssitem.itemslists[jsonstring([name, bot.type, ievent.channel])]
    except KeyError: ievent.reply("no itemslist set for (%s, %s)" % (name, ievent.channel)) ; return
    ievent.reply("itemslist of (%s, %s): " % (name, ievent.channel), itemslist)

cmnds.add('rss-itemslist', handle_rssitemslist, ['RSS', 'USER'])
examples.add('rss-itemslist', 'get itemslist of feed', 'rss-itemslist jsonbot')

## rss-scan command

def handle_rssscan(bot, ievent):
    """ scan rss item for used xml tokens. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    if not watcher.byname(name): ievent.reply('no %s feeds available' % name) ; return
    try: result = watcher.scan(name)
    except Exception, ex: ievent.reply(str(ex)) ; return
    if result == None: ievent.reply("can't get data for %s" % name) ; return
    res = []
    for i in result: res.append("%s=%s" % i)
    ievent.reply("tokens of %s: " % name, res)

cmnds.add('rss-scan', handle_rssscan, ['USER', ])
examples.add('rss-scan', 'rss-scan <name> .. get possible items of <name> ', 'rss-scan jsonbot')

## rss-sync command

def handle_rsssync(bot, ievent):
    """ sync rss item data. """
    try: name = ievent.args[0]
    except IndexError: ievent.missing('<name>') ; return
    if not watcher.ownercheck(name, ievent.userhost): ievent.reply("you are not the owner of the %s feed" % name) ; return
    result = watcher.sync(name)
    ievent.reply('%s synced' % name)

cmnds.add('rss-sync', handle_rsssync, ['USER', ], threaded=True)
examples.add('rss-sync', 'rss-sync <name> .. sync data of <name>', 'rss-sync jsonbot')

## rss-feeds

def handle_rssfeeds(bot, ievent):
    """ show what feeds are running in a channel. """
    try: channel = ievent.args[0]
    except IndexError: channel = ievent.channel
    result = watcher.getfeeds(bot.name, bot.type, channel)
    if result: ievent.reply("feeds running in %s: " % channel, result)
    else: ievent.reply('%s has no feeds running' % channel)

cmnds.add('rss-feeds', handle_rssfeeds, ['USER', 'RSS'])
examples.add('rss-feeds', 'rss-feeds <name> .. show what feeds are running in a channel', '1) rss-feeds 2) rss-feeds #dunkbots')

## rss-link command

def handle_rsslink(bot, ievent):
    """ search link entries in cached data. """
    try: feed, rest = ievent.rest.split(' ', 1)
    except ValueError: ievent.missing('<feed> <words to search>') ; return
    rest = rest.strip().lower()
    try:
        res = watcher.search(feed, 'link', rest)
        if not res: res = watcher.search(feed, 'feedburner:origLink', rest)
        if res: ievent.reply("link: ", res, dot=" \002||\002 ")
    except KeyError: ievent.reply('no %s feed data available' % feed) ; return

cmnds.add('rss-link', handle_rsslink, ['RSS', 'USER'])
examples.add('rss-link', 'give link of item which title matches search key', 'rss-link jsonbot gozer')

## rss-description commmand

def handle_rssdescription(bot, ievent):
    """ search descriptions in cached data. """
    try: feed, rest = ievent.rest.split(' ', 1)
    except ValueError: ievent.missing('<feed> <words to search>') ; return
    rest = rest.strip().lower()
    res = ""
    try: ievent.reply("results: ", watcher.search(feed, 'summary', rest))
    except KeyError: ievent.reply('no %s feed data available' % feed) ; return

cmnds.add('rss-description', handle_rssdescription, ['RSS', 'USER'])
examples.add('rss-description', 'give description of item which title \
matches search key', 'rss-description jsonbot gozer')

## rss-all command

def handle_rssall(bot, ievent):
    """ search titles of all cached data. """
    try: feed = ievent.args[0]
    except IndexError: ievent.missing('<feed>') ; return
    try: ievent.reply('results: ', watcher.all(feed, 'title'), dot=" \002||\002 ")
    except KeyError: ievent.reply('no %s feed data available' % feed) ; return

cmnds.add('rss-all', handle_rssall, ['RSS', 'USER'])
examples.add('rss-all', "give titles of a feed", 'rss-all jsonbot')

## rss-search

def handle_rsssearch(bot, ievent):
    """ search in titles of cached data. """
    try: txt = ievent.args[0]
    except IndexError: ievent.missing('<txt>') ; return
    try: ievent.reply("results: ", watcher.searchall('title', txt))
    except KeyError: ievent.reply('no %s feed data available' % feed) ; return

cmnds.add('rss-search', handle_rsssearch, ['RSS', 'USER'])
examples.add('rss-search', "search titles of all current feeds", 'rss-search goz')

def handle_rssimport(bot, ievent):
    """ import feeds uses OPML. """
    if not ievent.rest: ievent.missing("<url>") ; return
    import xml.etree.ElementTree as etree
    data = geturl2(ievent.rest)
    if not data: ievent.reply("can't fetch data from %s" % ievent.rest)
    try: element = etree.fromstring(data)
    except Exception, ex: ievent.reply("error reading %s: %s" % (ievent.rest, str(ex))) ; return
    teller = 0
    errors = {}
    for elem in element.getiterator():
        name = elem.get("keyname") or elem.get("text")
        if name: name = "+".join(name.split())
        url = elem.get('url') or elem.get("xmlUrl")
        try:
            assert(name)
            assert(url)
            logging.warn("rss - import - adding %s - %s" % (name, url))
            watcher.add(fromenc(name), fromenc(url), ievent.userhost)
            teller += 1
        except Exception, ex:
            errors[name] = str(ex)
    ievent.reply("added %s items" % teller)
    if errors:
        errlist = []
        for name, err in errors.iteritems():
            errlist.append("%s - %s" % (name, err))
        ievent.reply("there were errors: ", errlist)

cmnds.add('rss-import', handle_rssimport, ['OPER', ])
