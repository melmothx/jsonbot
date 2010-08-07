# plugs/wikipedia.py
#
#

""" query wikipedia .. use countrycode to select a country specific wikipedia. """

## gozerlib imports

from gozerlib.utils.url import geturl, striphtml
from gozerlib.utils.generic import splittxt, handle_exception, fromenc
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.rsslist import rsslist

## generic imports

from urllib import quote
import re

## defines

wikire = re.compile('start content(.*?)end content', re.M)

## functions

def searchwiki(txt, lang='en'):
    txt = txt.strip()
    for i in txt.split():
        if i.startswith('-'):
            if len(i) != 3:
                continue
            else:
                lang = i[1:]
            continue
    txt = txt.replace(u"-%s" % lang, '')
    txt = txt.capitalize()
    what = txt.replace(' ', '_')
    url = u'http://%s.wikipedia.org/wiki/Special:Export/%s' % (lang, \
quote(what.encode('utf-8')))
    url2 = u'http://%s.wikipedia.org/wiki/%s' % (lang, \
quote(what.encode('utf-8')))
    txt = getwikidata(url)
    if not txt:
        return ("", url2)
    if 'from other capitalisation' in txt:
        what = what.title()
        url = u'http://%s.wikipedia.org/wiki/Special:Export/%s' % (lang, \
quote(what.encode('utf-8')))
        url2 = u'http://%s.wikipedia.org/wiki/%s' % (lang, \
quote(what.encode('utf-8')))
        txt = getwikidata(url)
    if '#REDIRECT' in txt or '#redirect' in txt:
        redir = ' '.join(txt.split()[1:])
        url = u'http://%s.wikipedia.org/wiki/Special:Export/%s' % (lang, \
quote(redir.encode('utf-8')))
        url2 = u'http://%s.wikipedia.org/wiki/%s' % (lang, \
quote(redir.encode('utf-8')))
        txt = getwikidata(url)
    return (txt, url2)

def getwikidata(url):
    """ fetch wiki data """
    result = geturl(url)
    if not result:
        return
    res = rsslist(result)
    txt = ""
    for i in res:
        try:
            txt = i['text']
            break
        except:
            pass

    return txt

## commands

def handle_wikipedia(bot, ievent):
    """ <what> .. search wikipedia. """
    if not ievent.rest:
        ievent.missing('<what>')
        return
    res = searchwiki(ievent.rest)
    if not res[0]:
        ievent.reply('no result found')
        return

    txt, url = res
    txt = re.sub('\s+', ' ', txt)
    txt = re.sub('==(.*?)==', '<h3>\g<1></h3>', txt)
    txt = re.sub('\[\[(.*?)\]\]', '<b>\g<1></b>', txt)
    txt = re.sub('{{(.*?)}}', '<i>\g<1></i>', txt)
    txt = u'%s ===> %s' % (url, txt)
    txt = txt.replace('|', ' - ')

    ievent.reply(txt)

cmnds.add('wikipedia', handle_wikipedia, ['USER', 'GUEST'])
examples.add('wikipedia', 'wikipedia ["-" <countrycode>] <what> .. search \
wikipedia for <what>','1) wikipedia gozerbot 2) wikipedia -nl bot')
