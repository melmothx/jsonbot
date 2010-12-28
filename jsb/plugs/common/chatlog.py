# jsb.plugs.common/chatlog.py
#
#

"""
    log irc channels to [hour:min] <nick> txt format, only 
    logging to files is supported right now. 

"""

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.callbacks import callbacks, remote_callbacks
from jsb.lib.persistconfig import PersistConfig
from jsb.utils.locking import lockdec
from jsb.utils.timeutils import hourmin
from jsb.lib.examples import examples
from jsb.utils.exception import handle_exception
from jsb.utils.lazydict import LazyDict
from jsb.lib.datadir import getdatadir
from jsb.utils.name import stripname

## basic imports

import time
import os
import logging
import thread
from os import path
from datetime import datetime

## locks

outlock = thread.allocate_lock()
outlocked = lockdec(outlock)

## defines

cfg = PersistConfig()
cfg.define('channels', [])
cfg.define('format', 'simple')
cfg.define('basepath', getdatadir())
cfg.define('nologprefix', '[nolog]')
cfg.define('nologmsg', '-= THIS MESSAGE NOT LOGGED =-')
cfg.define('backend', 'file')

logfiles = {}
backends = {}
stopped = False
db = None

# Formats are defined here. simple also provides default values if values
# are not supplied by the format, as well as format 'simple'. 
# Parameters that should be supplied:
#   * timestamp_format: format of timestamp in log files
#     * all strftime vars supported.
#   * filename: file name for log
#     * var channel : full channel ie. #dunkbot
#     * var channel_name : channel without '#' ie. dunkbot
#   * event_filename: 
#        if event_filename exists, then it will be used for
#        logging events (seperate from chat)
#     * var channel : full channel ie. #dunkbot
#     * var channel_name : channel without '#' ie. dunkbot
#   * separator: the separator between the timestamp and message

formats = {
    'simple': {
        'timestamp_format': '%Y-%m-%d %H:%M:%S',
        'basepath': None,
        'filename': 'chatlogs/%%(network)s/simple/%%(target)s.%Y%m%d.slog',
        'event_prefix': '',
        'event_filename': 'chatlogs/%%(network)s/simple/%%(channel_name)s.%Y%m%d.slog',
        'separator': ' | ',
    },
    'supy': {
        'timestamp_format': '%Y-%m-%dT%H:%M:%S',
        'filename': 'chatlogs/%%(network)s/supy/%%(target)s/%%(target)s.%Y-%m-%d.log',
        'event_prefix': '*** ',
        'event_filename': None,
        'separator': '  ',
    }
}

## functions

def format_opt(name):
    simple_format = formats['simple']
    format = formats.get(cfg.get('format'), 'simple')
    opt = format.get(name, simple_format.get(name, None))
    return opt

def init():
    global stopped
    stopped = False
    callbacks.add('ALL', chatlogcb, prechatlogcb)
    remote_callbacks.add('ALL', chatlogcb, prechatlogcb)
    return 1

def shutdown():
    global stopped
    stopped = True
    for file in logfiles.values():
        file.close()
    return 1

def timestr(dt):
    return dt.strftime(format_opt('timestamp_format'))

@outlocked
def write(m): 
    """
      m is a dict with the following properties:
      datetime
      type : (comment, nick, topic etc..)
      target : (#channel, bot etc..)
      txt : actual message
      network
    """
    backend_name = cfg.get('backend', 'file')
    backend = backends.get(backend_name, file_write)
    if m['txt'].startswith(cfg.get('nologprefix')): m['txt'] = cfg.get('nologmsg')
    backend(m)

def file_write(m):
    if stopped: return
    args = {
        'target': m.get('target'), 
        'network': m.get('network'), 
        'logdir': cfg.get('logdir')
    }
    #if args['target'][0] in "#":
    #    args['target'] = u"-" + args['target'][1:]
    args['channel_name'] = args['target'] 
    #else: args['channel_name'] = args['target']
    f = time.strftime(format_opt('filename')) % args
    if m['type'] != 'comment':
        event_filename = format_opt('event_filename')
        if event_filename: f = time.strftime(event_filename) % args
        m['txt'] = '%s%s'%(m['event_prefix'], m['txt'])
    else: m['txt'] = '<%s> %s'%(m['nick'], m['txt'])
    basepath = cfg.get('basepath')
    if basepath: f = path.join(basepath, f)
    dir = path.dirname(f)
    if not path.exists(dir):
         try: os.makedir(dir)
         except: pass
    timestamp = timestr(m['datetime'])
    line = '%(timestamp)s%(separator)s%(txt)s\n'%({
        'timestamp': timestamp, 
        'separator': format_opt('separator'),
        'txt': m['txt'],
    })
    try:
        if logfiles.has_key(f):
            logfiles[f].write(line)
            logfiles[f].flush()
        else:
            logging.warn('chatlog - opening %s for logging'%(f))
            logfiles[f] = open(f, 'a')
            logfiles[f].write(line)
            logfiles[f].flush()
    except Exception, ex: handle_exception()

backends['file'] = file_write

## log function

def formatevent(bot, ievent):
    m = {
        'datetime': datetime.now(),
        'separator': format_opt('separator'),
        'event_prefix': format_opt('event_prefix'),
        'network': bot.networkname,
        'nick': ievent.nick,
        'target': stripname(ievent.channel),
    }
    m = LazyDict(m)

    if ievent.cbtype == "OUTPUT":
        m.update({
            'type': 'output',
            'txt': ievent.txt
        })
    elif ievent.cmnd == 'PRIVMSG':
        if ievent.txt.startswith('\001ACTION'):
            m.update({
                'type': 'action',
                'txt': '* %s %s'%(m['nick'], ievent.txt[7:-1].strip()),
            })
        else:
            m.update({
                'type': 'comment',
                'txt': '%s'%(ievent.txt),
            })
    elif ievent.cmnd == 'NOTICE':
        m.update({
            'type': 'notice',
            'target': ievent.arguments[0],
            'txt': "-%s- %s"%(ievent.nick, ievent.txt)
        })
    elif ievent.cmnd == 'TOPIC':
        m.update({
            'type': 'topic',
            'txt': '%s changes topic to "%s"'%(ievent.nick, ievent.txt),
        })
    elif ievent.cmnd == 'MODE':
        margs = ' '.join(ievent.arguments[1:])
        m.update({
            'type': 'mode',
            'txt': '%s sets mode: %s'%(ievent.nick, margs),
        })
    elif ievent.cmnd == 'JOIN':
        m.update({
            'type': 'join',
            'txt': '%s (%s) has joined %s'%(ievent.nick, ievent.userhost, ievent.channel),
        })
    elif ievent.cmnd == 'KICK':
        m.update({
            'type': 'kick',
            'txt': '%s was kicked by %s (%s)'%(
                ievent.arguments[1], 
                ievent.nick, 
                ievent.txt
            ),
        })
    elif ievent.cmnd == 'PART':
        m.update({
            'type': 'part',
            'txt': '%s (%s) has left'%(ievent.nick, ievent.userhost),
        })
    elif ievent.cmnd in ('QUIT', 'NICK'):
        if not ievent.user or not ievent.user.data.channels:
            logging.debug("chatlog - can't find joined channels for %s" % ievent.userhost)
            return m
        cmd = ievent.cmnd
        nick = cmd == 'NICK' and ievent.txt or ievent.nick
        for c in event.user.channels:
            if [bot.name, c] in cfg.get('channels'):
                if True:
                    if cmd == 'NICK':
                        m['txt'] = '%s (%s) is now known as %s'%(
                            ievent.nick, ievent.userhost, ievent.txt
                        )
                    else:
                        m['txt'] = '%s (%s) has quit: %s'%(
                            ievent.nick, ievent.userhost, ievent.txt
                        )
                    m.update({
                        'type': ievent.cmnd.lower(),
                        'target': c,
                    })
                    write(m)
        return m
    elif ievent.cbtype == 'MESSAGE':
            m.update({
                'type': 'comment',
                'txt': ievent.txt.strip(),
            })
    elif ievent.cbtype == 'PRESENCE':
            if ievent.type == 'unavailable':
                m.update({
                    'type': 'part',
                    'txt': "%s left"%ievent.nick
                })
            else:
                m.update({
                    'type': 'join',
                    'txt': "%s joined"%ievent.nick
                })
    elif ievent.cbtype == 'BLIP_SUBMITTED':
            m.update({
                'type': 'blip',
                'txt': ievent.txt.strip(),
            })
    elif ievent.cbtype == 'DISPATCH':
            m.update({
                'type': 'dipatch',
                'txt': ievent.txt,
            })

    return m

def log(bot, event):
    m = formatevent(bot, event)
    if m.get('txt'):
        write(m)

## chatlog precondition

def prechatlogcb(bot, ievent):
    """Check if event should be logged.  QUIT and NICK are not channel
    specific, so we will check each channel in log()."""
    if bot.isgae: return False
    if not cfg.channels:
        return False
    if not ievent.msg and [bot.name, ievent.channel] in cfg.get('channels'):
        return True
    if ievent.cmnd in ('QUIT', 'NICK'):
        return True
    if ievent.cmnd == 'NOTICE':
        if [bot.name, ievent.arguments[0]] in cfg.get('channels'):
            return True

## chatlog callbacks

def chatlogcb(bot, ievent):
    log(bot, ievent)

## chatlog-on command

def handle_chatlogon(bot, ievent):
    """ enable chatlog. """
    chan = ievent.channel
    if [bot.name, chan] not in cfg.get('channels'):
        cfg['channels'].append([bot.name, chan])
        cfg.save()
        ievent.reply('chatlog enabled on (%s,%s)' % (bot.name, chan))
    else: ievent.reply('chatlog already enabled on (%s,%s)' % (bot.name, chan))

cmnds.add('chatlog-on', handle_chatlogon, 'OPER')
examples.add('chatlog-on', 'enable chatlog on <channel> or the channel \
the commands is given in', '1) chatlog-on 2) chatlog-on #dunkbots')

## chatlog-off command

def handle_chatlogoff(bot, ievent):
    """ disable chatlog. """
    try:
        cfg['channels'].remove([bot.name, ievent.channel])
        cfg.save()
    except ValueError:
        ievent.reply('chatlog is not enabled in (%s,%s)' % (bot.name, ievent.channel))
        return
    ievent.reply('chatlog disabled on (%s,%s)' % (bot.name, ievent.channel))

cmnds.add('chatlog-off', handle_chatlogoff, 'OPER')
examples.add('chatlog-off', 'disable chatlog on <channel> or the channel the commands is given in', '1) chatlog-off 2) chatlog-off #dunkbots')