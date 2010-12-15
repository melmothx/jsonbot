# gozerlib/utils/generic.py
#
#

""" generic functions. """

## lib imports 

from exception import handle_exception
from trace import calledfrom, whichmodule
from lazydict import LazyDict
from gozerlib.contrib.simplejson import dumps

## generic imports

from stat import ST_UID, ST_MODE, S_IMODE
import time
import sys
import re
import getopt
import types
import os
import os.path
import random
import Queue 
import logging

## isdebian function

def isdebian():
    """ checks if we are on debian. """
    return os.path.isfile("/etc/debian_version")

## isjsonbotuser function

def botuser():
    """ checks if the user is jsonbot. """
    try:
        import getpass
        return getpass.getuser() 
    except ImportError: return ""

## checkpermission function

def checkpermissions(ddir, umode):
    """ see if ddir has umode permission and if not set them. """
    try:
        uid = os.getuid()
        gid = os.getgid()
    except AttributeError: return
    try: stat = os.stat(ddir)
    except OSError: return
    if stat[ST_UID] != uid:
        try: os.chown(ddir, uid, gid)
        except: pass
    if S_IMODE(stat[ST_MODE]) != umode:
        try: os.chmod(ddir, umode)
        except: handle_exception()

## jsonstring function

def jsonstring(s):
    """ convert s to a jsonstring. """
    if type(s) == types.TupleType: s = list(s)
    return dumps(s)

## getwho function

def getwho(bot, who):
    """ get userhost from bots userhost cache """
    who = who.lower()
    for user in bot.userhosts:
        if user.lower() == who: return bot.userhosts[user]

## splitxt function

def splittxt(what, l=375):
    """ split output into seperate chunks. """
    txtlist = []
    start = 0
    end = l
    length = len(what)
    for i in range(length/end+1):
        starttag = what.find("</", end)
        if starttag != -1: endword = what.find('>', end) + 1
        else:
            endword = what.find(' ', end)
            if endword == -1: endword = length
        res = what[start:endword]
        if res: txtlist.append(res)
        start = endword
        end = start + l
    return txtlist

## getrandomnick function
    
def getrandomnick():
    """ return a random nick. """
    return "jsonbot-" + str(random.randint(0, 100))

## decodeperchar function

def decodeperchar(txt, encoding='utf-8', what=""):
    """ decode a string char by char. strip chars that can't be decoded. """
    res = []
    nogo = []
    for i in txt:
        try: res.append(i.decode(encoding))
        except UnicodeDecodeError:
            if i not in nogo: nogo.append(i)
    if nogo:
        if what: logging.debug("%s: can't decode %s characters to %s" % (what, nogo, encoding))
        else: logging.debug("%s - can't decode %s characters to %s" % (whichmodule(), nogo, encoding))
    return u"".join(res)

## toenc function

def toenc(what, encoding='utf-8'):
    """ convert to encoding. """
    if not what: what=  u""
    try:
        w = unicode(what)
        return w.encode(encoding)
    except UnicodeDecodeError:
        logging.debug("%s - can't encode %s to %s" % (whichmodule(2), what, encoding))
        raise

## fromenc function

def fromenc(txt, encoding='utf-8', what=""):
    """ convert from encoding. """
    if not txt: txt = u""
    try: return txt.decode(encoding)
    except UnicodeDecodeError:
        logging.debug("%s - can't decode %s - decoding per char" % (whichmodule(), encoding))
        return decodeperchar(txt, encoding, what)

## toascii function

def toascii(what):
    """ convert to ascii. """
    return what.encode('ascii', 'replace')

## tolatin1 function

def tolatin1(what):
    """ convert to latin1. """
    return what.encode('latin-1', 'replace')

## strippedtxt function

def strippedtxt(what, allowed=[]):
    """ strip control characters from txt. """
    txt = []
    for i in what:
        if ord(i) > 31 or (allowed and i in allowed): txt.append(i)
    return ''.join(txt)

## uniqlist function

def uniqlist(l):
    """ return unique elements in a list (as list). """
    result = []
    for i in l:
        if i not in result: result.append(i)
    return result

## jabberstrip function

def jabberstrip(text, allowed=[]):
    """ strip control characters for jabber transmission. """
    txt = []
    allowed = allowed + ['\n', '\t']
    for i in text:
        if ord(i) > 31 or (allowed and i in allowed): txt.append(i)
    return ''.join(txt)

## filesize function

def filesize(path):
    """ return filesize of a file. """
    return os.stat(path)[6]

## touch function

def touch(fname):
    """ touch a file. """
    fd = os.open(fname, os.O_WRONLY | os.O_CREAT)
    os.close(fd)  

## stringinlist function

def stringinlist(s, l):
    """ check is string is in list of strings. """
    for i in l:     
        if s in i: return True
    return False

## stripped function

def stripped(userhost):
    """ return a stripped userhost (everything before the '/'). """ 
    return userhost.split('/')[0]

## gethighest function

def gethighest(ddir, ffile):
    """ get filename with the highest extension (number). """
    highest = 0
    for i in os.listdir(ddir):
        if os.path.isdir(ddir + os.sep + i) and ffile in i:
            try: seqnr = i.split('.')[-1]
            except IndexError: continue
            try:
                if int(seqnr) > highest: highest = int(seqnr)
            except ValueError: pass
    ffile += '.' + str(highest + 1)
    return ffile

## waitforqueue function

def waitforqueue(queue, timeout=50, maxitems=None):
    """ wait for results to arrive in a queue. return list of results. """
    result = []
    counter = 0
    while 1:
        try: res = queue.get_nowait()
        except Queue.Empty:
            time.sleep(0.1)
            counter += 1
            if counter > timeout: break
            continue
        if res == None: break 
        result.append(res)
        if maxitems and len(result) == maxitems: break
    return result

## checkqueues function

def checkqueues(self, queues, resultlist):
    """ check if resultlist is to be sent to the queues. if so do it! """
    for queue in queues:
        for item in resultlist: queue.put_nowait(item)
        return True
    return False

## dosed function

def dosed(filename, sedstring):
    """ apply a sedstring to the file. """
    try: f = open(filename, 'r')
    except IOError: return
    tmp = filename + '.tmp'
    fout = open(tmp, 'w')
    seds = sedstring.split('/')   
    fr = seds[1].replace('\\', '')
    to = seds[2].replace('\\', '')
    try:
        for line in f:
            if 'googlecode' in line: l = line
            else: l = line.replace(fr,to)
            fout.write(l)
    finally:
        fout.flush()
        fout.close()
    try: os.rename(tmp, filename)
    except WindowsError:
        os.remove(filename)
        os.rename(tmp, filename)
