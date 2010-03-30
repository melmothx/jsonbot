# gozerlib/utils/id.py
#
#

from gozerlib.utils.generic import toenc
import uuid

def getrssid(url, time):
    key = unicode(url) + unicode(time)
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, toenc(key)))

