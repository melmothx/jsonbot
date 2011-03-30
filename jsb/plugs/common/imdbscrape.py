## jsb imports

from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2, striphtml, decode_html_entities
from urllib import quote
import logging
import re

baseurl = 'http://www.imdb.com'


def do_imdb_title_search(query):
    """fetch the page with the search, appending the parameters string"""
    url = baseurl + '/search/title?' + query
    logging.warn(url)
    return geturl2(url)

#http://www.imdb.com/search/title?release_date=1984,1992&sort=user_rating&title=terminator

def scan_query(userstring):
    params = map(quote, userstring.split())
    minyear = None
    maxyear = None
    query = ""
    if len(params) > 2:
        lastparam = params.pop()
        if not re.match("^\d{4}$", lastparam):
            params.append(lastparam)
        else:
            maxyear = lastparam
        # and again
        lastparam = params.pop()
        if not re.match("^\d{4}$", lastparam):
            params.append(lastparam)
        else:
            minyear = lastparam

    elif len(params) > 1:
        lastparam = params.pop()
        if not re.match("^\d{4}$", lastparam):
            params.append(lastparam)
        else:
            maxyear = lastparam

    query = '+'.join(params)
    if maxyear and minyear:
        date = minyear + ',' + maxyear
    elif maxyear:
        date = maxyear + ',' + maxyear
    else:
        date = None
    return { 'title': query,
             'release_date': date,
             'sort': 'user_rating' # fixed
             }

def build_query(querydict):
    outstring = ""
    query_list = []
    for k, v in querydict.iteritems():
        if v:
            token = k + '=' + v
            query_list.append(token)
    return "&".join(query_list)

def scrape_it(garbage):
    strings = garbage.split('\n')
    out = []
    result = re.compile(r'<a href="(?P<url>/title/tt[0-9]+?/)" *title="(?P<title>.*?)"')
    for line in strings:
        l = result.search(line)
        if l:
            out.append({'url': l.group('url'),
                        'title': l.group('title')})
    # return the first 5 results
    return out[:5]

# def scrape_imdb_entry(url):

def handle_imdb_scraping(bot, event):
    if not event.rest: 
        event.missing("<query>")
        return
    query = build_query(scan_query(event.rest.strip()))
    results = scrape_it(do_imdb_title_search(query))
    # print results
    out = []
    for index, title in enumerate(results):
        myindex = index + 1
        out.append("(%d.)" % myindex)
        out.append("%(title)s: http://imdb.org%(url)s" % title)
    event.reply(" | ".join(out))

cmnds.add("imdb2", handle_imdb_scraping, ["OPER", "USER", "GUEST"])

