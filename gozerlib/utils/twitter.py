# gozerlib/utils/twitter.py
#
#

""" twitter related helper functions .. uses tweepy. """

## tweppy imports

from tweepy.auth import OAuthHandler
from tweepy.api import API
from tweepy import oauth  

go = True

## basic imports

import logging 

def twitterapi(CONSUMER_KEY, CONSUMER_SECRET, token=None, *args, **kwargs):
    if not go:
        logging.warn("the twitter plugin needs the credentials.py file in the gozerdata/config dir. see gozerdata/examples".upper())
        return None
    if token:
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(token.key, token.secret)

    return API(auth, *args, **kwargs)

def twittertoken(CONSUMER_KEY, CONSUMER_SECRET, twitteruser, username):
    token = twitteruser.data.get(username)
    if not token:
        return
    return oauth.OAuthToken(CONSUMER_KEY, CONSUMER_SECRET).from_string(token)
    
