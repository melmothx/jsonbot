# commonplugs/twitter.py
#
#

""" a twitter plugin for the JSONBOT. """


## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.datadir import datadir
from gozerlib.examples import examples
from gozerlib.utils.pdol import Pdol
from gozerlib.utils.textutils import html_unescape
from gozerlib.utils.generic import waitforqueue
from gozerlib.contrib.oauthtwitter import OAuthApi
from gozerlib.contrib.twitter import TwitterError, User
from gozerlib.persist import PlugPersist
from gozerdata.config.credentials import CONSUMER_KEY, CONSUMER_SECRET
from gozerlib.contrib.twitterauth import OAuthHandler
import gozerlib.contrib.oauth as oauth


## basic imports

import os
import urllib2

## functions

def twitterapi(token=None, *args, **kwargs):
    if token:
        api = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET, token, *args, **kwargs)
    else:
        api = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET, *args, **kwargs)
       
    #api.SetXTwitterHeaders('gozerbot', 'http://gozerbot.org', __version__)
    return api

## defines

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

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
        result = [ievent.rest, ]

    try:
        twitteruser = TwitterUser("users")
        token = twitteruser.data.get(ievent.userhost)
        if not token:
            ievent.reply("you are not logged in yet .. run the twitter-auth command.")
            return 
        token = oauth.OAuthToken(CONSUMER_KEY, CONSUMER_SECRET).from_string(token)
        twitter = twitterapi(token)

        for txt in result:
            status = twitter.PostUpdate(txt[:119])
        ievent.reply("zooi posted.")    
    except KeyError:
        handle_exception()
        ievent.reply('you are not logged in yet. see the twitter-auth command.')
    except (TwitterError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter', handle_twitter, 'USER')
examples.add('twitter', 'adds a message to your twitter account', 'twitter just found the http://gozerbot.org project')

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
    twitteruser.add(ievent.userhost, access_token.to_string())
    ievent.reply("access token saved.")

cmnds.add('twitter-confirm', handle_twitter_confirm, 'TWITTER')
examples.add('twitter-confirm', 'confirm your twitter account', '1) twitter-confirm 6992762')

def handle_twitter_auth(bot, ievent):

    """ set twitter id. """

    try:
        auth_url = auth.get_authorization_url()
    except (TwitterError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))
        return
    ievent.reply("sign in at %s" % auth_url)
    ievent.reply("use the provided code in the twitter-confirm command.")

cmnds.add('twitter-auth', handle_twitter_auth, 'TWITTER')
examples.add('twitter-auth', 'adds your twitter account', '1) twitter-auth')
