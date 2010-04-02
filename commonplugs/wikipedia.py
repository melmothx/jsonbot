# plugs/wikipedia.py
#
#

""" query wikipedia .. use -<countrycode> to select a country 
    specific wikipedia. 
"""

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
    for i in txt.split():
        if i.startswith('-'):
            if len(i) != 3:
                continue
            else:
                lang = i[1:]
            continue
    txt = txt.replace("-%s" % lang, '')
    txt = txt.strip().capitalize()
    what = txt.strip().replace(' ', '_')
    url = 'http://%s.wikipedia.org/wiki/Special:Export/%s' % (lang, \
quote(what.encode('utf-8')))
    url2 = 'http://%s.wikipedia.org/wiki/%s' % (lang, \
quote(what.encode('utf-8')))
    txt = getwikidata(url)
    if not txt:
        return None
    if 'from other capitalisation' in txt:
        what = what.title()
        url = 'http://%s.wikipedia.org/wiki/Special:Export/%s' % (lang, \
quote(what.encode('utf-8')))
        url2 = 'http://%s.wikipedia.org/wiki/%s' % (lang, \
quote(what.encode('utf-8')))
        txt = getwikidata(url)
    if '#REDIRECT' in txt or '#redirect' in txt:
        redir = ' '.join(txt.split()[1:])
        url = 'http://%s.wikipedia.org/wiki/Special:Export/%s' % (lang, \
quote(redir.encode('utf-8')))
        url2 = 'http://%s.wikipedia.org/wiki/%s' % (lang, \
quote(redir.encode('utf-8')))
        txt = getwikidata(url)
    return (txt, url2)

def getwikidata(url):
    """ fetch wiki data """
    result = fromenc(geturl(url))
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
    if not txt:
        return
    #txt = re.sub('\[\[Image:([^\[\]]+|\[\[[^\]]+\]\])*\]\]', '', txt)
    txt = txt.replace('[[', '')
    txt = txt.replace(']]', '')
    txt = re.sub('\s+', ' ', txt)
    return txt

## commands

def handle_wikipedia(bot, ievent):
    """ <what> .. search wikipedia. """
    if not ievent.rest:
        ievent.missing('<what>')
        return
    res = searchwiki(ievent.rest)
    if not res:
        ievent.reply('no result found')
        return
    txt, url = res
    prefix = '%s ===> ' % url
    result = splittxt(striphtml(txt).strip())
    ievent.reply(prefix, result, raw=True)

cmnds.add('wikipedia', handle_wikipedia, ['USER', 'GUEST'])
examples.add('wikipedia', 'wikipedia ["-" <countrycode>] <what> .. search \
wikipedia for <what>','1) wikipedia gozerbot 2) wikipedia -nl bot')
