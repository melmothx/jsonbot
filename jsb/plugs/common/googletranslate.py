## jsb imports

from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2, striphtml, decode_html_entities
from jsb.imports import getjson
import logging
import re
from urllib import quote

# URL = "http://imdbapi.poromenos.org/js/?name=%s" # for this tweaking is needed, but it doesn't appear to work as adviced. E.g., inception return None
URL = r"http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&q=%(text)s&langpair=%(from)s|%(to)s"

def parse_pair(text):
    trans = re.match("^(?P<from>[a-z]{2}) +(?P<to>[a-z]{2}) +(?P<txt>.*)$",
                     text)
    return {'from': trans.group('from'),
            'to':   trans.group('to'),
            'text': quote(trans.group('txt'))}

def handle_translate(bot, event):
    if not event.rest: 
        event.missing("<from> <to> <text>")
        return
    query = parse_pair(event.rest.strip())
    if not query: 
        event.missing("<from> <to> <text>")
        return
#    event.reply(URL % query)
    rawresult = {}
    rawresult = getjson().loads(geturl2(URL % query))
#    rawresult = {"responseData": {"translatedText":"test"}, "responseDetails": None, "responseStatus": 200}
    logging.warn(URL % query)
    logging.warn(rawresult)
    translation = rawresult['responseData']['translatedText']
    event.reply(translation)

cmnds.add("translate", handle_translate, ["OPER", "USER", "GUEST"])

