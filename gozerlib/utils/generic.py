# lib/utils/generic.py
#
#

""" generic functions. """

## lib imports 

from exception import handle_exception
from trace import calledfrom, whichmodule
from lazydict import LazyDict
from gozerlib.datadir import datadir

## simplejson import

from simplejson import dumps

## generic imports

from stat import ST_UID, ST_MODE, S_IMODE
import time
import sys
import re
import getopt
import types
import os
import random
import Queue 
import logging

## functions

def checkpermissions(ddir, umode):
    try:
        uid = os.getuid()
        gid = os.getgid()
    except AttributeError:
        return
    try:
        stat = os.stat(ddir)
    except OSError:
        return
    if stat[ST_UID] != uid:
        try:
            os.chown(ddir, uid, gid)
        except:
            pass
    if S_IMODE(stat[ST_MODE]) != umode:
        try:
            os.chmod(ddir, umode)
        except:
            handle_exception()
            pass


def jsonstring(s):
    if type(s) == types.TupleType:
        s = list(s)
    return dumps(s)

def getwho(bot, who):
    """ get userhost from bots userhost cache """
    who = who.lower()
    for user in bot.userhosts:
        if user.lower() == who:
            return bot.userhosts[user]

def getversion(txt=""):

    """ return a version string. """

    from gozerlib.config import cfg
    return u"%s" % (cfg.get('version') + u' ' + txt)

def splittxt(what, l=375):
    """ split output into seperate chunks. """
    txtlist = []
    start = 0
    end = l
    length = len(what)
    for i in range(length/end+1):
        starttag = what.find("</", end)
        if starttag != -1:
            endword = what.find('>', end) + 1
        else:
            endword = what.find(' ', end)
            if endword == -1:
                endword = length

        res = what[start:endword]
        if res:
            #logging.warn(u"splittxt - adding %s (%s)" % (unicode(res), len(res)))
            txtlist.append(res)

        start = endword
        end = start + l

    return txtlist
    
def getrandomnick():
    """ return a random nick. """

    return "jsonbot-" + str(random.randint(0, 100))

def decodeperchar(txt, encoding='utf-8', what=""):
    """ decode a string char by char. strip chars that can't be decoded. """
    res = []
    nogo = []

    for i in txt:
        try:
            res.append(i.decode(encoding))
        except UnicodeDecodeError:
            if i not in nogo:
                nogo.append(i)
            continue

    if nogo:
        if what:
            logging.debug("%s: can't decode %s characters to %s" % (what, nogo, encoding))
        else:
            logging.debug("%s - can't decode %s characters to %s" % (whichmodule(), nogo, encoding))

    return u"".join(res)

def toenc(what, encoding='utf-8'):
    """ convert to encoding. """
    if not what:
        what=  u""

    try:
        w = unicode(what)
        return w.encode(encoding)
    except UnicodeDecodeError:
        logging.debug("%s - can't encode %s to %s" % (whichmodule(2), what, encoding))
        raise
        #return u""

def fromenc(txt, encoding='utf-8', what=""):
    """ convert from encoding. """
    if not txt:
        txt = u""

    try:
        #if type(txt) == types.UnicodeType:
        #    t = txt
            #t = txt.encode(encoding)
        #else:
        #    t = unicode(txt)
        return txt.decode(encoding)
    except UnicodeDecodeError:
        logging.debug("%s - can't decode %s" % (whichmodule(), encoding))
        #raise
        return decodeperchar(txt, encoding, what)

def toascii(what):
    """ convert to ascii. """
    what = what.encode('ascii', 'replace')
    return what

def tolatin1(what):
    """ convert to latin1. """
    what = what.encode('latin-1', 'replace')

    return what

def strippedtxt(what, allowed=[]):
    """ strip control characters from txt. """
    txt = []
    for i in what:
        if ord(i) > 31 or (allowed and i in allowed):
            txt.append(i)

    return ''.join(txt)

def uniqlist(l):
    """ return unique elements in a list (as list). """
    result = []
    for i in l:
        if i not in result:
            result.append(i)

    return result

def jabberstrip(text, allowed=[]):
    """ strip control characters for jabber transmission. """
    txt = []
    allowed = allowed + ['\n', '\t']

    for i in text:
        if ord(i) > 31 or (allowed and i in allowed):
            txt.append(i)

    return ''.join(txt)

def filesize(path):
    """ return filesize of a file. """

    return os.stat(path)[6]

def touch(fname):
    """ touch a file. """
    fd = os.open(fname, os.O_WRONLY | os.O_CREAT)
    os.close(fd)  

def stringinlist(s, l):
    """ check is string is in list of strings. """
    for i in l:     
        if s in i:  
            return 1

def stripped(userhost):
    """ return a stripped userhost (everything before the '/'). """ 

    return userhost.split('/')[0]

def gethighest(ddir, ffile):
    """ get filename with the highest extension (number). """
    highest = 0
    for i in os.listdir(ddir):
        if os.path.isdir(ddir + os.sep + i) and ffile in i:

            try:
                seqnr = i.split('.')[-1]
            except IndexError:
                continue

            try:
                if int(seqnr) > highest:
                    highest = int(seqnr)
            except ValueError:
                pass

    ffile += '.' + str(highest + 1)

    return ffile

def waitforqueue(queue, timeout=10, maxitems=None):
    """ wait for results to arrive in a queue. return list of results. """
    result = []
    counter = 0
    while 1:

        try:   
            res = queue.get_nowait()
        except Queue.Empty:
            time.sleep(0.1)
            counter += 1
            if counter > timeout*10:
                break
            continue

        if not res:
            break 

        result.append(res)

        if maxitems and len(result) == maxitems:
            break

    return result

def checkqueues(self, queues, resultlist):
    """ check if resultlist is to be sent to the queues. if so do it! """
    for queue in queues:
        for item in resultlist:
            queue.put_nowait(item)

        return True
    return False

def dosed(filename, sedstring):
    try:
        f = open(filename, 'r')
    except IOError:
        return
    tmp = filename + '.tmp'
    fout = open(tmp, 'w')
    seds = sedstring.split('/')   
    fr = seds[1].replace('\\', '')
    to = seds[2].replace('\\', '')
    try:
        for line in f:
            if 'googlecode' in line:
                l = line
            else:
                l = line.replace(fr,to)
            fout.write(l)
    finally:
        fout.flush()
        fout.close()
    try:
        os.rename(tmp, filename)
    except WindowsError:
        # no atomic operation supported on windows! error is thrown when destination exists
        os.remove(filename)
        os.rename(tmp, filename)
