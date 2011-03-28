# jsb/plugs/common/geo.py
#
#

""" This product includes GeoLite data created by MaxMind, available from http://maxmind.com/ """


## jsb imports

from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2
from jsb.imports import getjson

## system imports
from socket import gethostbyname
import re
## defines

URL = "http://geoip.pidgets.com/?ip=%s&format=json"

def querygeoipserver(ip):
    ipinfo = getjson().loads(geturl2(URL % ip))
    return ipinfo

## geo command

def handle_geo(bot, event):
    if not event.rest: 
        event.missing("<ip>")
        return
    query = event.rest.strip()
    ippattern =   re.match(r"^([0-9]{1,3}\.){3}[0-9]{1,3}$", query)
    hostpattern = re.match(r"(\w+://)?(?P<hostname>\S+\.\w+)", query)
    ip = ""
    if ippattern:
        ip = ippattern.group(0)

    elif hostpattern:
        try: 
            ip = gethostbyname(hostpattern.group('hostname'))
        except:
            event.reply("Couldn't look up the hostname")
            return

    else: return

    event.reply("geo of %s is: " % ip, querygeoipserver(ip))



cmnds.add("geo", handle_geo, ["OPER", "GEO"])
