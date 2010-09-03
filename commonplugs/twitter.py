# Twitter post plugin
# (c) Wijnand 'maze' Modderman <http://tehmaze.com>
# BSD License
#
# I included the Twitter API, because I had to fix some minor issues. These
# issues have been reported so maybe the API part will be removed from this
# plugin at a later stadium.
#
# 4-9-2010 Change to use oauth (bthate@gmail.com)


## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.datadir import datadir
from gozerlib.examples import examples
from gozerlib.utils.pdol import Pdol
from gozerlib.utils.textutils import html_unescape
from gozerlib.utils.generic import waitforqueue
from gozerlib.contrib.oauthtwitter import OAuthApi
from gozerlib.contrib.twitter import TwitterError, User
from gozerdata.config.credentials import CONSUMER_KEY, CONSUMER_SECRET

## basic imports

import os
import urllib2

## defines

__version__ = '0.3'

## functions

def twitterapi(token=None, *args, **kwargs):
    if token:
        api = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET, token, *args, **kwargs)
    else:
        api = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET, *args, **kwargs)
       
    #api.SetXTwitterHeaders('gozerbot', 'http://gozerbot.org', __version__)
    return api

## classes

class TwitterUser(Pdol):
    def __init__(self):
        Pdol.__init__(self, os.path.join(datadir + os.sep + 'plugs' + \
os.sep + 'commonplugs.twitter', 'twitter'))

    def add(self, user, username, password):
        self.data[user] = [username, password]
        self.save()

    def remove(self, user):
        if user in self.data:
            del self.data[user]
            self.save()

    def size(self):
        return len(self.data)

    def __contains__(self, user):
        return user in self.data


## more defines

twitteruser = TwitterUser()

def size():
    return twitteruser.size()

def handle_twitter(bot, ievent):

    """ send a twitter message. """

    #if not ievent.user in twitteruser:
    #    ievent.reply('you need a twitter account for this command, '
    #                 'use "!twitter-id <username> <password>"'
    #                 'first (in a private message!)')
    #    return
    #if ievent.inqueue:
    #    result = waitforqueue(ievent.inqueue, 30)
    if not ievent.rest:
        ievent.missing('<text>')
        return
    else:
        result = [ievent.rest, ]

    try:
        token = twitteruser.get(ievent.channel)
        if not token:
            ievent.reply("you are not logged in yet .. run the twitter-auth command.")
            return
        api = twitterapi()
        access_token = api.getAccessToken()
        twitter = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET, access_token)

        for txt in result:
            status = twitter.PostUpdate(txt[:119])

    except (TwitterError, urllib2.HTTPError), e:
        ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter', handle_twitter, 'USER')
examples.add('twitter', 'adds a message to your twitter account', 
    'twitter just found the http://gozerbot.org project')

def handle_twitter_friends(bot, ievent):

    """ show twitter friends. """

    if not ievent.user in twitteruser:
        ievent.reply('you need a twitter account for this command, '
                     'use "!twitter-id <username> <password>" '
                     'first (in a private message!)')
    else:
        credentials = twitteruser.get(ievent.channel)
        try:
            api = twitterapi(username=credentials[0], password=credentials[1])
            users = api.GetFriends()
            users = ['%s (%s)' % (u.name, u.screen_name) for u in users]
            if users:
                users.sort()
                ievent.reply('your twitter friends: ', users, dot=True)
            else:
                ievent.reply('poor you, no friends!')
        except Exception, e:
            ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter-friends', handle_twitter_friends, 'USER')
examples.add('twitter-friends', 'shows your twitter friends', 'twitter-friends')

def handle_twitter_get(bot, ievent):

    """ get twitter messages. """

    if not ievent.args:
        ievent.missing('<username>')
    else:
        try:
            credentials = twitteruser.get(ievent.channel)
            api = twitterapi()
            statuses = api.GetUserTimeline(ievent.args[0])
            for status in statuses:
                if status.name == ievent.args[0]:
                    ievent.reply([html_unescape(s.text) for s in status], dot=True)
                    return
            ievent.reply('no result')
        except (TwitterError, urllib2.HTTPError), e:
            ievent.reply('twitter failed: %s' % (str(e),))

cmnds.add('twitter-get', handle_twitter_get, 'USER')
examples.add('twitter-get', 'gets the twitter messages for a user', 'twitter-get tehmaze')

def handle_twitter_confirm(bot, ievent):

    """ set twitter id. """

    twitteruser.add(ievent.channel, ievent.args[0], "")
    ievent.done()

cmnds.add('twitter-confirm', handle_twitter_confirm, 'TWITTER')
examples.add('twitter-confirm', 'confirm your twitter account', '1) twitter-confirm 6992762')

def handle_twitter_auth(bot, ievent):

    """ set twitter id. """

    api = twitterapi()
    request_token = api.getRequestToken()
    signin_url = api.getSigninURL(request_token)
    ievent.reply("sign in at %s and use the provided code in the twitter-confirm command." % signin_url)

cmnds.add('twitter-auth', handle_twitter_auth, 'TWITTER')
examples.add('twitter-auth', 'adds your twitter account', '1) twitter-auth')
