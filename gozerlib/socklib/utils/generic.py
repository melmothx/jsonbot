# gozerlib/socklib/utils/generic.py
#
#

""" generic functions """


## gozerlib imports

from gozerlib.persist import Persist
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.trace import calledfrom
from gozerlib.config import cfg as config
from gozerlib.utils.lazydict import LazyDict

## simplejson

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
import socket
import Queue 
import logging

def jsonstring(s):
    if type(s) == types.TupleType:
        s = list(s)
    return dumps(s)

def stripident(userhost):
    """ strip ident char from userhost """
    try:
        userhost.getNode()
        return str(userhost)
    except AttributeError:  
        pass
    if not userhost:
        return None 
    if userhost[0] in "~-+^":
        userhost = userhost[1:]
    elif userhost[1] == '=':   
        userhost = userhost[2:]
    return userhost

def stripidents(ulist):
    """ strip ident char from list of userhosts """
    result = []
    for userhost in ulist:
        result.append(stripident(userhost))
    return result

def makedirs(datadir):
    if not os.path.isdir(datadir):
        os.mkdir(datadir)
    if not os.path.isdir(datadir + '/states/'):    
        os.mkdir(datadir + '/states/')    
    if not os.path.isdir(datadir + '/db/'):
        os.mkdir(datadir + '/db/')
    if not os.path.isdir(datadir + '/configs/'):
        os.mkdir(datadir + '/configs/')

def getversion():
    version = config['version']
    if config['nodb']:
        version += ' JSON_USERS'
    else:
        version += ' ' + config['dbtype'].upper()
    return version

def makeoptions(ievent, options={}):
    options = LazyDict(options)
    try:
        optargs = ""
        optlist = []
        if not options.has_key('--filter'):
            options['--filter'] = ""
        if not options.has_key('--to'):
            options['--to'] = None
        if not options.has_key('--chan'):
            options['--chan'] = ievent.channel
        if not options.has_key('--how'):
            options['--how'] = "msg"
        if not options.has_key('--speed'):
            options['--speed'] = str(ievent.speed)
        else:
            options['--speed'] = str(options['--speed'])
        for i, j in options.iteritems():
            if '--' in i:
                optlist.append("%s=" % i[2:])
                if j:
                    optlist.append(j)
                continue
            if '-' in i:
                if j:
                    optargs += ":%s" % i[1:]
                else:
                    optargs += i[1:]
        args = ievent.txt.split()
        try:
            (opts, rest) = getopt.getopt(args[1:], optargs, optlist)
        except AttributeError, ex:
            print "option not allowed: %s" % str(ex), ievent.txt, options
            return 0
        except getopt.GetoptError, ex:
            return 0
        if opts:
             for item in opts:
                 ievent.optionset.append(item[0])
        o = dict(options)
        o.update(dict(opts))
        try:
            filter = o['--filter']
            if filter and filter not in ievent.filter:
                ievent.filter.append(filter)
        except KeyError:
            pass
        try:
            speed = o['--speed']
            ievent.speed = int(speed)
        except KeyError:
            pass
        try:
            ievent.channel = o['--chan'] or ievent.channel
        except KeyError:
            pass
        ievent.options.update(o)
        if args:
            ievent.txt = args[0] + ' ' + ' '.join(rest)
        makeargrest(ievent)
    except Exception, ex:
        handle_exception()
        return 
    return ievent.options

def makeargrest(ievent):
    """ create ievent.args and ievent.rest .. this is needed because \
         ircevents might be created outside the parse() function """

    if not ievent.txt:
        return

    try:
        ievent.args = ievent.txt.split()[1:]
    except ValueError:
        ievent.args = []   

    try:
        cmnd, ievent.rest = ievent.txt.split(' ', 1)
    except ValueError:   
        ievent.rest = ""   

    ievent.usercmnd = ievent.txt.split()[0]

def setdefenc(encoding):
    import sys
    reload(sys)
    sys.setdefaultencoding(encoding)

def plugfile(datadir):
    return datadir + os.sep + calledfrom(sys._getframe())

def cchar(bot, ievent):
    try:
        cchar = bot.channels[ievent.channel]['cc']
    except LookupError:
        cchar = config['defaultcc'] or '!'
    except TypeError:
        cchar = config['defaultcc'] or '!'
    return cchar

def splittxt(what, l=375):
    txtlist = []
    start = 0
    end = l
    length = len(what)
    for i in range(length/end+1):
        endword = what.find(' ', end)
        if endword == -1:
            endword = length
        res = what[start:endword]
        if res:
            txtlist.append(res)
        start = endword
        end = start + l
    return txtlist
    
class istr(str): 
    pass

def die():
    os.kill(os.getpid(), 9)

def getlistensocket(listenip):
    port = 5000
    while 1:
        time.sleep(0.01)
        try:
            port += 1
            if ':' in listenip:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(1)
            if port > 65000:
                port = 5000
            sock.bind((listenip, port))
            sock.listen(1)
            return (port, sock)
        except Exception, ex:
            pass

def checkchan(bot, item):
    chanre = re.search(' chan (\S+)', item)
    if chanre:
        chan = str(chanre.group(1))
        item = re.sub(' chan ' + re.escape(chan), '', item)
        return (chan.lower(), item)

def getwho(bot, who):
    """ get userhost from bots userhost cache """
    try:
        result = bot.userhosts[who]
        if bot.cfg['stripident']:
            logging.debug('getwho - removed ident from %s' % result)
            result = stripident(result)
        return result
    except KeyError:
        return None

def waitforuser(bot, userhost, timeout=15):
    queue = Queue.Queue()
    waitnr = bot.privwait.register(userhost, queue, timeout)
    result = queue.get()
    bot.privwait.delete(waitnr)
    return result

def getrandomnick():
    return "jsb-" + str(random.randint(0, 100))

def waitforqueue(queue, timeout=10, maxitems=None):
    result = []
    while 1:
        try:
            res = queue.get(1, timeout)
        except Queue.Empty:
            break
        if not res:
            break
        result.append(res)
        if maxitems and len(result) == maxitems:
            break
    return result

def decodeperchar(txt, encoding='utf-8', what=""):

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
            logging.debug("generic - %s: can't decode %s characters to %s" % (what, nogo, encoding))
        else:
            logging.debug("generic - can't decode %s characters to %s" % (nogo, encoding))

    return u"".join(res)

def toascii(what):
    what = what.encode('ascii', 'replace')
    return what

def tolatin1(what):
    what = what.encode('latin-1', 'replace')
    return what

def strippedtxt(what, allowed=[]):
    txt = []
    allowed = allowed + ['\001', '\002', '\003', '\t']
    for i in what:
        if ord(i) > 31 or (allowed and i in allowed):
            txt.append(i)
    return ''.join(txt)

def uniqlist(l):
    result = []
    for i in l:
        j = i.strip()
        if j not in result:
            result.append(j)
    return result

def fix_format(s):
    counters = {
        chr(2): 0, 
        chr(3): 0
        }
    for letter in s:
        if letter in counters:
            counters[letter] += 1
    for char in counters:
        if counters[char] % 2:
            s += char
    return s

def stripbold(s):
    s = s.replace(chr(2), '')
    s = s.replace(chr(3), '')
    return s

def jabberstrip(text, allowed=[]):
    txt = []
    allowed = allowed + ['\n', '\t']
    for i in text:
        if ord(i) > 31 or (allowed and i in allowed):
            txt.append(i)
    return ''.join(txt)

def plugnames(dirname):
    result = []
    for i in os.listdir(dirname):
        if os.path.isdir(dirname + os.sep + i):
            if os.path.exists(dirname + os.sep + i + os.sep + '__init__.py'):
                result.append(i)
        elif i.endswith('.py'):
            result.append(i[:-3])
    try:
        result.remove('__init__')
    except:
        pass
    return result

def filesize(path):
    return os.stat(path)[6]

def touch(fname):
    fd = os.open(fname, os.O_WRONLY | os.O_CREAT)
    os.close(fd)  

def stringinlist(s, l):
    for i in l:     
        if s in i:  
            return 1

def stripped(userhost):
    return userhost.split('/')[0]

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

def gethighest(ddir, ffile):
    highest = 0
    for i in os.listdir(ddir):
        if os.path.isdir(ddir + os.sep + i) and ffile in i:
            try:
                seqnr = i.split('.')[2]
            except IndexError:
                continue
            try:
                if int(seqnr) > highest:
                    highest = int(seqnr)
            except ValueError:
                pass
    ffile += '.' + str(highest + 1)
    return ffile

def dosed(filename, sedstring):
    try:
        f = open(filename, 'r')
    except IOError, ex:
        if 'Is a dir' in str(ex):
            return
        else:
            raise
    tmp = filename + '.tmp'
    fout = open(tmp, 'w')
    seds = sedstring.split('/')
    fr = seds[1].replace('\\', '')
    to = seds[2].replace('\\', '')
    try:
        for line in f:
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

def convertpickle(src, target):
    import gozerbot.compat.persist
    p = gozerbot.compat.persist.Persist(src)    
    if p and p.data:
        pers = Persist(target)
        if not pers.data:
            pers.data = {}
        pers.data.update(p.data)
        try:
            pers.save()
        except TypeError:
            pers2 = Persist(target)
            if not pers2.data:
                pers2.data = {}
            for item, value in p.data.iteritems():
                pers2.data[jsonstring(item)] = value
            pers2.save()
