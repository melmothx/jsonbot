# gozerlib/utils/web.py
#
#

""" google auth related functions. """

## gozerlib imports

from gozerlib.utils.trace import whichmodule

## google imports

from google.appengine.api import users as gusers

## basic imports

import logging

## functions

def finduser():
    """ try to find the email of the current logged in user. """
    user = gusers.get_current_user()
    if user:
        return user.email()

    return "" 

def checkuser(response, request):
    """
        check for user based on web response. first try google 
        otherwise return 'notath@IP' 

        :param response: response object
        :param request: request object
        :rtype: tuple of (userhost, gmail user, bot user , nick)

    """
    userhost = "notauth"
    u = "notauth"
    nick = "notauth"
    user = gusers.get_current_user()

    if not user:
        try:
            email = request.get('USER_EMAIL')
            if not email:
                email = "notauth"
            auth_domain = request.get('AUTH_DOMAIN')
            if not auth_domain:
                auth_domain = "nodomain"
            who = request.get('who')
            if not who:
                 who = email
            userhost = nick = "%s!%s@%s" % (who, auth_domain, request.remote_addr)

        except KeyError:
            userhost = nick = "notauth@%s" % request.remote_addr
    else:
        userhost = user.email() 
        if not userhost:
            userhost = nick = "notauth@%s" % request.remote_addr
        nick = user.nickname()
        u = userhost

    cfrom = whichmodule()
    if 'gozerlib' in cfrom:
        cfrom = whichmodule(1)
        if 'gozerlib' in cfrom: 
            cfrom = whichmodule(2)

    logging.warn("auth - %s - %s - %s - %s - %s" % (cfrom, userhost, user, u, nick))
    return (userhost, user, u, nick)
