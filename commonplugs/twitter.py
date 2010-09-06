# commonplugs/twitter.py
#
#

""" a twitter plugin for the JSONBOT. uses tweepy oauth. """


## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.datadir import datadir
from gozerlib.examples import examples
from gozerlib.utils.pdol import Pdol
from gozerlib.utils.textutils import html_unescape
from gozerlib.utils.generic import waitforqueue, strippedtxt, splittxt
from gozerlib.persist import PlugPersist

## tweppy imports

from tweepy.auth import OAuthHandler
from tweepy.api import API
from tweepy import oauth
from tweepy.error import TweepError
from tweepy.models import Status

## credentials

go = True

try:
    from gozerdata.config.credentials import CONSUMER_KEY, CONSUMER_SECRET
except ImportError:
    raise Exception("the twitter plugin needs the credentials.py file in the gozerdata/config dir. see gozerdata/examples")

## basic imports

import os
import urllib2

## defines

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

def twitterapi(token=None, *args, **kwargs):
    if token:
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(token.key, token.secret)
    return API(auth, *args, **kwargs)

## classes

class TwitterUser(PlugPersist):

    def add(self, user, token):
        user = user.strip().lower()
        self.data[user] = token
        self.save()

    def remove(self, user):
        user = user.strip().lower()
        if user in self.data:
            del self.data[user]
            self.save()

    def size(self):
        return len(self.data)

    def __contains__(self, user):
        user = user.strip().lower()
        return user in self.data


## commands

def handle_twitter(bot, ievent):

    """ send a twitter message. """

    #if ievent.inqueue:
    #    result = waitforqueue(ievent.inqueue, 30)
    if not ievent.rest:
        ievent.missing('<text>')
        return
    else:
        result = splittxt(ievent.rest, 120)

    try:
        twitteruser = TwitterUser("users")
        token = twitteruser.data.get(ievent.user.data.name)
        if not token:
            ievent.reply("you are not logged in yet .. run the twitter-auth command.")
            return 
        token = oauth.OAuthToken(CONSUMER_KEY, CONSUMER_SECRET).from_string(token)
        twitter = twitterapi(token)
        
        for txt in result:
            status = twitter.update_status(txt[:119])
        ievent.reply("%s tweet posted." % len(result))
    except KeyError:
        handle_exception()
        ievent.reply('you are not logged in yet. see the twitter-auth command.')
    except (TweepError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter', handle_twitter, 'USER')
examples.add('twitter', 'adds a message to your twitter account', 'twitter just found the http://gozerbot.org project')

def handle_twittercmnd(bot, ievent):

    """ send a twitter message. """

    #if ievent.inqueue:
    #    result = waitforqueue(ievent.inqueue, 30)
    if not ievent.args:
        ievent.missing('<text>')
        return

    target =  strippedtxt(ievent.args[0])

    try:
        twitteruser = TwitterUser("users")
        token = twitteruser.data.get(ievent.user.data.name)
        if not token:
            ievent.reply("you are not logged in yet .. run the twitter-auth command.")
            return 
        token = oauth.OAuthToken(CONSUMER_KEY, CONSUMER_SECRET).from_string(token)
        twitter = twitterapi(token)
        try:
            
            method = getattr(twitter, target)
        except AttributeError:
            ievent.reply("choose one of: %s" % str(dir(twitter)))
            return

        # do the thing
        result = method()
        ievent.reply(result) 
    except KeyError:
        handle_exception()
        ievent.reply('you are not logged in yet. see the twitter-auth command.')
    except (TwitterError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter-cmnd', handle_twittercmnd, 'USER')
examples.add('twitter-cmnd', 'do a cmnd on the twitter API', 'twitter-cmnd home_timeline')

def handle_twitter_confirm(bot, ievent):

    """ set twitter id. """

    pin = ievent.args[0]
    if not pin:
        ievent.missing("<PIN> .. see the twitter-auth command.")
        return
    try:
        access_token = auth.get_access_token(pin)
    except (TwitterError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))
        return
    twitteruser = TwitterUser("users")
    twitteruser.add(ievent.user.data.name, access_token.to_string())
    ievent.reply("access token saved.")

cmnds.add('twitter-confirm', handle_twitter_confirm, ['USER', 'OPER'])
examples.add('twitter-confirm', 'confirm your twitter account', '1) twitter-confirm 6992762')

def handle_twitter_auth(bot, ievent):

    """ set twitter id. """

    try:
        auth_url = auth.get_authorization_url()
    except (TwitterError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))
        return
    if bot.type == "irc":
        bot.say(ievent.nick, "sign in at %s" % auth_url)
        bot.say(ievent.nick, "use the provided code in the twitter-confirm command.")
    else:
        ievent.reply("sign in at %s" % auth_url)
        ievent.reply("use the provided code in the twitter-confirm command.")

cmnds.add('twitter-auth', handle_twitter_auth, ['USER', 'OPER'])
examples.add('twitter-auth', 'adds your twitter account', '1) twitter-auth')
