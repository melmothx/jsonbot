## jsb imports

from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2
from jsb.imports import getjson
import logging


URL = "http://www.deanclatworthy.com/imdb/?q=%s"

def handle_imdb(bot, event):
    if not event.rest: 
        event.missing("<query>")
        return
    logging.warn(event.rest)
    query = event.rest.strip()
    result = getjson().loads(geturl2(URL % query))
#    result = resultdict['imdburl']
    event.reply("%s: " % query, result)

cmnds.add("imdb", handle_imdb, ["OPER", "USER", "GUEST"])

