## jsb imports

from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2, striphtml, decode_html_entities
from jsb.imports import getjson
import logging


URL = "http://www.deanclatworthy.com/imdb/?q=%s"


def handle_imdb(bot, event):
    if not event.rest: 
        event.missing("<query>")
        return
    query = event.rest.strip()
    rawresult = getjson().loads(geturl2(URL % query))

# the API are limited to 30 query per hour, so avoid querying it just for 
# testing purposes

#    rawresult = {u'ukscreens': 0, u'rating': u'7.7', u'genres': u'Animation,&nbsp;Drama,Family,Fantasy,Music', u'title': u'Pinocchio', u'series': 0, u'country': u'USA', u'votes': u'23209', u'languages': u'English', u'stv': 0, u'year': u'1940', u'usascreens': 0, u'imdburl': u'http://www.imdb.com/title/tt0032910/'}
    result = {u'title':     u"n/a",
              u'country':   u"n/a",
              u'year':      u"n/a",
              u'imdburl':   u"n/a",
              u'rating':    u"n/a",
              u'votes':     u"n/a",
              u'genres':    u"n/a",
              u'languages': u"n/a"}
    logging.warn(rawresult, result)
    for key in result.keys():
        result[key] = striphtml(decode_html_entities(rawresult[key]))


    event.reply("%(title)s (%(country)s, %(year)s): %(imdburl)s | rating:\
 %(rating)s (out of %(votes)s votes) | Genres %(genres)s | Language: %(languages)s" 
                % {"title": result['title'],
                   "country": result['country'],
                   "year": result['year'],
                   "imdburl": result['imdburl'],
                   "rating": result['rating'],
                   "votes": result['votes'],
                   "genres": result['genres'],
                   "languages": result['languages']})

cmnds.add("imdb", handle_imdb, ["OPER", "USER", "GUEST"])

