# gozerlib/plugs/login.py
#
#

from gozerlib.commands import public, cmnds
from gozerlib.examples import examples
from gozerlib.gae.utils.auth import checkuser
from gozerlib.gae.utils.web import loginurl

def handle_loginurls(bot, event):
    if not event.response or not event.request:
        event.reply("this command only works on web bots. ")
        return

    (userhost, user, u, nick) = checkuser(event.response, event.request, event)
    urlstring = ""
    for name, url in loginurl(event.request, event.response).iteritems():
        urlstring += '<a href="%s"><b>%s</b></a> - ' % (url, name)
    if not urlstring:
        login = "can't log in"
    elif user:
        login = u"switch: %s" % urlstring[:-3]
    else:
        login = u"please log in: %s" % urlstring[:-3]
    event.reply(login, raw=True)

cmnds.add('login-urls', handle_loginurls, ['USER', 'OPER', 'GUEST'])
public.add('login-urls', handle_loginurls, ['USER', 'OPER', 'GUEST'])
examples.add('login-urls', 'display openid logins', 'login-url')
