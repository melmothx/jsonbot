## jsb imports

from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2, striphtml, decode_html_entities
from jsb.imports import getjson
from urllib import quote
import logging
import re

def do_imdb_api_query(query):
    url = "http://www.deanclatworthy.com/imdb/?" + query
    logging.warn(url)
    result = getjson().loads(geturl2(url))
    return result
 
def scan_query(userstring):
    params = map(quote, userstring.split())
    yg = "1"
    year = None
    query = ""
    if len(params) > 1:
        lastparam = params.pop()
        if not re.match("^\d{4}$", lastparam):
            params.append(lastparam)
        else:
            year = lastparam
            yg = "0"

    query = '+'.join(params)
    return { 'q': query,
             'year': year,
             'yg': yg,
             'type': "json",
             }

def build_query(querydict):
    outstring = ""
    query_list = []
    for k, v in querydict.iteritems():
        if v:
            token = k + '=' + v
            query_list.append(token)
    return "&".join(query_list)


def handle_imdb(bot, event):
    if not event.rest: 
        event.missing("<query>")
        return
    query = build_query(scan_query(event.rest.strip()))
    result = {}
    rawresult = do_imdb_api_query(query)

# the API are limited to 30 query per hour, so avoid querying it just for 
# testing purposes

#    rawresult = {u'ukscreens': 0, u'rating': u'7.7', u'genres': u'Animation,&nbsp;Drama,Family,Fantasy,Music', u'title': u'Pinocchio', u'series': 0, u'country': u'USA', u'votes': u'23209', u'languages': u'English', u'stv': 0, u'year': None, u'usascreens': 0, u'imdburl': u'http://www.imdb.com/title/tt0032910/'}
    if not rawresult:
        event.reply("Couldn't look up %s" % query)
        return

    if 'error' in rawresult:
        event.reply("%s" % rawresult['error'])
        return

    for key in rawresult.keys():
        if not rawresult[key]:
            result[key] = u"n/a"
        else:
            result[key] = rawresult[key]

    logging.warn(rawresult, result)
    for key in result.keys():
        try:
            result[key] = striphtml(decode_html_entities(rawresult[key]))
        except AttributeError:
            # if the value is not a string, ignore the error and keep going
            pass

    event.reply("%(title)s (%(country)s, %(year)s): %(imdburl)s | rating:\
 %(rating)s (out of %(votes)s votes) | Genres %(genres)s | Language: %(languages)s" % result )

cmnds.add("imdb", handle_imdb, ["OPER", "USER", "GUEST"])

