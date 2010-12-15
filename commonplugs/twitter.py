# commonplugs/twitter.py
#
#

""" a twitter plugin for the JSONBOT. uses tweepy oauth. """


## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.pdol import Pdol
from gozerlib.utils.textutils import html_unescape
from gozerlib.utils.generic import waitforqueue, strippedtxt, splittxt
from gozerlib.persist import PlugPersist
from gozerlib.utils.twitter import twitterapi, twittertoken
from gozerlib.datadir import getdatadir
from gozerlib.jsbimport import _import_byfile

## tweppy imports

from gozerlib.contrib.tweepy.auth import OAuthHandler
from gozerlib.contrib.tweepy.api import API
from gozerlib.contrib.tweepy import oauth
from gozerlib.contrib.tweepy.error import TweepError
from gozerlib.contrib.tweepy.models import Status, User
from gozerlib.contrib import tweepy

go = True

## basic imports

import os
import urllib2
import types
import logging

## credentials

def getcreds(datadir):
    try:
        mod = _import_byfile("credentials", datadir + os.sep + "config" + os.sep + "credentials.py")
    except (IOError, ImportError):
        logging.info("the twitter plugin needs the credentials.py file in the %s/config dir. see %s/examples" % (datadir, datadir))
        return (None, None)
    return mod.CONSUMER_KEY, mod.CONSUMER_SECRET

## defines

auth = None

def getauth(datadir):
    global auth
    if auth: return auth
    key, secret = getcreds(datadir)
    auth = OAuthHandler(key, secret)
    return auth

## functions

def postmsg(username, txt):
    result = splittxt(txt, 139)
    twitteruser = TwitterUsers("users")
    key, secret = getcreds(getdatadir())
    token = twittertoken(key, secret, twitteruser, username)
    if not token:
        raise TweepError("Can't get twitter token")
    twitter = twitterapi(key, secret, token)
    for txt in result:
        status = twitter.update_status(txt)
    # BHJTW need to check status
    return len(result)
    
## classes

class TwitterUsers(PlugPersist):

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

    if not go:
        ievent.reply("the twitter plugin needs the credentials.py file in the gozerdata/config dir. see gozerdata/examples")
        return
    if not ievent.rest:
        ievent.missing('<text>')
        return
    else:
        try:
             nritems = postmsg(ievent.user.data.name, ievent.rest)
             ievent.reply("%s tweet posted" % nritems)
        except TweepError, ex:
             if "token" in str(ex): ievent.reply("you are not registered yet.. use !twitter-auth")
        except (TweepError, urllib2.HTTPError), e:
            ievent.reply('twitter failed: %s' % (str(e),))
 
cmnds.add('twitter', handle_twitter, ['USER', 'GUEST'])
examples.add('twitter', 'adds a message to your twitter account', 'twitter just found the http://gozerbot.org project')

def handle_twittercmnd(bot, ievent):
    """ do a twitter API cmommand. """
    if not go:
        ievent.reply("the twitter plugin needs the credentials.py file in the gozerdata/config dir. see gozerdata/examples")
        return
    if not ievent.args:
        ievent.missing('<text>')
        return

    target =  strippedtxt(ievent.args[0])

    try:
        twitteruser = TwitterUsers("users")
        token = twitteruser.data.get(ievent.user.data.name)
        if not token:
            ievent.reply("you are not logged in yet .. run the twitter-auth command.")
            return 
        key, secret = getcreds(getdatadir())
        token = oauth.OAuthToken(key, secret).from_string(token)
        twitter = twitterapi(key, secret, token)
        cmndlist = dir(twitter)
        cmnds = []
        for cmnd in cmndlist:
            if cmnd.startswith("_") or cmnd == "auth":
                continue
            else:
                cmnds.append(cmnd)
        if target not in cmnds:
            ievent.reply("choose one of: %s" % ", ".join(cmnds))
            return

        try:
            
            method = getattr(twitter, target)
        except AttributeError:
            ievent.reply("choose one of: %s" % ", ".join(cmnds))
            return

        # do the thing
        result = method()
        res = []

        for item in result:
            try:
                res.append("%s - %s" % (item.screen_name, item.text))
            except AttributeError:
                try:
                    res.append("%s - %s" % (item.screen_name, item.description))
                except AttributeError:
                    try:
                        res.append(unicode(item.__getstate__()))
                    except AttributeError:
                        res.append(dir(i))
                        res.append(unicode(item))

        ievent.reply("result of %s: " % target, res) 
    except KeyError:
        #handle_exception()
        ievent.reply('you are not logged in yet. see the twitter-auth command.')
    except (TweepError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter-cmnd', handle_twittercmnd, 'OPER')
examples.add('twitter-cmnd', 'do a cmnd on the twitter API', 'twitter-cmnd home_timeline')

def handle_twitter_confirm(bot, ievent):
    """ confirm auth with PIN. """
    if not go:
        ievent.reply("the twitter plugin needs the credentials.py file in the %s/config dir. see gozerdata/examples" % getdatadir())
        return

    pin = ievent.args[0]
    if not pin:
        ievent.missing("<PIN> .. see the twitter-auth command.")
        return
    try:
        access_token = getauth(getdatadir()).get_access_token(pin)
    except (TweepError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))
        return
    twitteruser = TwitterUsers("users")
    twitteruser.add(ievent.user.data.name, access_token.to_string())
    ievent.reply("access token saved.")

cmnds.add('twitter-confirm', handle_twitter_confirm, ['USER', 'GUEST'])
examples.add('twitter-confirm', 'confirm your twitter account', '1) twitter-confirm 6992762')

def handle_twitter_auth(bot, ievent):
    """ get auth url. """
    if not go:
        ievent.reply("the twitter plugin needs the credentials.py file in the gozerdata/config dir. see gozerdata/examples")
        return

    try:
        auth_url = getauth(getdatadir()).get_authorization_url()
    except (TweepError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))
        return
    if bot.type == "irc":
        bot.say(ievent.nick, "sign in at %s" % auth_url)
        bot.say(ievent.nick, "use the provided code in the twitter-confirm command.")
    else:
        ievent.reply("sign in at %s" % auth_url)
        ievent.reply("use the provided code in the twitter-confirm command.")

cmnds.add('twitter-auth', handle_twitter_auth, ['USER', 'GUEST'])
examples.add('twitter-auth', 'adds your twitter account', '1) twitter-auth')

def handle_twitterfriends(bot, ievent):
    """ do a twitter API cmommand. """
    if not go:
        ievent.reply("the twitter plugin needs the credentials.py file in the gozerdata/config dir. see gozerdata/examples")
        return

    try:
        twitteruser = TwitterUsers("users")
        token = twitteruser.data.get(ievent.user.data.name)
        if not token:
            ievent.reply("you are not logged in yet .. run the twitter-auth command.")
            return 
        key , secret = getcreds(getdatadir())
        token = oauth.OAuthToken(key, secret).from_string(token)
        twitter = twitterapi(key, secret, token)
        method = getattr(twitter, "friends_timeline")

        # do the thing
        result = method()
        res = []
        for item in result:
            try:
                res.append("%s - %s" % (item.author.screen_name, item.text))
                #logging.warn("twitter - %s" % dir(item.author))
                #res.append(unicode(item.__getstate__()))
            except Exception, ex:
                handle_exception()

        ievent.reply("results: ", res) 
    except KeyError:
        #handle_exception()
        ievent.reply('you are not logged in yet. see the twitter-auth command.')
    except (TweepError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter-friends', handle_twitterfriends, ['USER', 'GUEST'])
examples.add('twitter-friends', 'show your friends_timeline', 'twitter-friends')
