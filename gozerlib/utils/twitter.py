# gozerlib/utils/twitter.py
#
#

""" twitter related helper functions .. uses tweepy. """

## tweepy imports

from tweepy.auth import OAuthHandler
from tweepy.api import API
from tweepy import oauth  

## basic imports

import logging 

## defines

go = True

## twitterapi function

def twitterapi(CONSUMER_KEY, CONSUMER_SECRET, token=None, *args, **kwargs):
    """ return twitter API object - with or without access token. """
    if not go:
        logging.warn("the twitter plugin needs the credentials.py file in the gozerdata/config dir. see gozerdata/examples".upper())
        return None
    if token:
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(token.key, token.secret)
    return API(auth, *args, **kwargs)

## twittertoken function

def twittertoken(CONSUMER_KEY, CONSUMER_SECRET, twitteruser, username):
    """ get access token from stored token string. """
    token = twitteruser.data.get(username)
    if not token: return
    return oauth.OAuthToken(CONSUMER_KEY, CONSUMER_SECRET).from_string(token)
