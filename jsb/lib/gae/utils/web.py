# jsb/utils/web.py
#
#

""" web related functions. """

## jsb imports

from jsb.utils.generic import fromenc
from jsb.lib.version import getversion
from jsb.lib.config import Config
from jsb.lib.channelbase import ChannelBase
from jsb.utils.lazydict import LazyDict

## gaelib imports

from auth import finduser

## basic imports

import os
import time
import socket
import urlparse

## defines

openIdProviders = [
    'Gmail.com',
    'Google.com',
    'Yahoo.com',
    'MySpace.com',
    'AOL.com',
    'MyOpenID.com',
]

## create_openid_url

def create_openid_url(continue_url):
    continue_url = urlparse.urljoin(self.request.url, continue_url)
    return "/_ah/login?continue=%s" % urllib.quote(continue_url)

## mini

def mini(response, input={}):
    """ display start html so that bot output can follow. """
    inputdict = LazyDict({'version': getversion()})
    if input: inputdict.update(input)
    temp = os.path.join(os.getcwd(), 'templates/mini.html')
    outstr = template.render(temp)
    response.out.write(outstr)

## start

def start(response, input={}):
    """ display start html so that bot output can follow. """
    try: host = socket.gethostname()
    except AttributeError:
         if os.environ.get('HTTP_HOST'): host = os.environ['HTTP_HOST']
         else: host = os.environ['SERVER_NAME']
    template = LazyDict({'version': getversion(), 'host': host, 'color': Config().color or "#C54848"})
    if input: template.update(input)
    temp = os.path.join(os.getcwd(), 'templates/console.html')
    outstr = template.render(temp)
    response.out.write(outstr)

## login

def login(response, input={}):
    """ display start html so that bot output can follow. """
    try: host = socket.gethostname()
    except AttributeError:
         if os.environ.get('HTTP_HOST'): host = os.environ['HTTP_HOST']
         else: host = os.environ['SERVER_NAME']
    template = LazyDict({'version': getversion(), 'host': host, 'color': Config().color or "#C54848"})
    if input: template.update(input)
    temp = os.path.join(os.getcwd(), 'templates/login.html')
    outstr = template.render(temp)
    response.out.write(outstr)

## commandbox (testing purposes)

def commandbox(response, url="/dispatch/"):
    """ write html data for the exec box. """
    response.out.write("""
          <form action="%s" method="post">
            <div><b>enter command:</b> <input type="commit" name="content"></div>
          </form>
          """ % url)

## commandbox (testing purposes)

def execbox(response, url="/exec/"):
    """ write html data for the exec box. """
    response.out.write("""
      <form action="" method="GET">
        <b>enter command:</b><input type="commit" name="input" value="">
        // <input type="button" value="go" onClick="makePOSTRequest(this.form)"
      </form>
          """)

## closer

def closer(response):
    """ send closing html .. comes after the bot output. """
    response.out.write('</div><div class="footer">')
    response.out.write('<b>%4f seconds</b></div>' % (time.time() - response.starttime))
    response.out.write('</body></html>')

## loginurl

def loginurl(request, response):
    """ return google login url. """
    from google.appengine.api import users as gusers
    urls = {}
    for p in openIdProviders:
        p_name = p.split('.')[-2]
        p_url = p.lower()
        try:
            url = gusers.create_login_url(federated_identity=p_url)
            if not url: url = create_openid_url(p_url)
        except TypeError: continue
        urls[p_name] = url
    return urls

## logouturl

def logouturl(request, response):
    """ return google login url. """
    from google.appengine.api import users as gusers
    return gusers.create_logout_url(request.uri)
