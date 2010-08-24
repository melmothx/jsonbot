# gozerlib/utils/web.py
#
#

""" web related functions. """

## gozerlib imports

from gozerlib.utils.generic import fromenc, getversion

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

## functions

def create_openid_url(continue_url):
    continue_url = urlparse.urljoin(self.request.url, continue_url)
    return "/_ah/login?continue=%s" % urllib.quote(continue_url)

def mini(response, input={}):
    """ display start html so that bot output can follow. """
    from google.appengine.ext.webapp import template
    inputdict = {'version': getversion()}
    if input:
        inputdict.update(input)
    temp = os.path.join(os.getcwd(), 'templates/mini.html')
    outstr = template.render(temp, inputdict)
    response.out.write(outstr)

def start(response, input={}):
    """ display start html so that bot output can follow. """
    try:
         host = socket.gethostname()
    except AttributeError:
         if os.environ.get('HTTP_HOST'):
             host = os.environ['HTTP_HOST']
         else:
             host = os.environ['SERVER_NAME']

    inputdict = {'version': getversion(), 'host': host}

    if input:
        inputdict.update(input)

    temp = os.path.join(os.getcwd(), 'templates/start.html')

    from google.appengine.ext.webapp import template
    outstr = template.render(temp, inputdict)

    response.out.write(outstr)

def login(response, input={}):
    """ display start html so that bot output can follow. """
    try:
         host = socket.gethostname()
    except AttributeError:
         if os.environ.get('HTTP_HOST'):
             host = os.environ['HTTP_HOST']
         else:
             host = os.environ['SERVER_NAME']

    inputdict = {'version': getversion(), 'host': host}

    if input:
        inputdict.update(input)

    temp = os.path.join(os.getcwd(), 'templates/login.html')

    from google.appengine.ext.webapp import template
    outstr = template.render(temp, inputdict)

    response.out.write(outstr)

def commandbox(response, url="/dispatch/"):
    """ write html data for the exec box. """
    response.out.write("""
          <form action="%s" method="post">
            <div><b>enter command:</b> <input type="commit" name="content"></div>
          </form>
          """ % url)

def execbox(response, url="/exec/"):
    """ write html data for the exec box. """
    response.out.write("""
      <form action="" method="GET">
        <b>enter command:</b><input type="commit" name="input" value="">
        // <input type="button" value="go" onClick="makePOSTRequest(this.form)"
      </form>
          """)

def closer(response):
    """ send closing html .. comes after the bot output. """
    response.out.write('</div><div class="footer">')
    response.out.write('<b>%4f seconds</b></div>' % (time.time() - response.starttime))
    response.out.write('</body></html>')

def loginurl(request, response):
    """ return google login url. """
    from google.appengine.api import users as gusers
    urls = {}
    for p in openIdProviders:
        p_name = p.split('.')[-2] # take "AOL" from "AOL.com"
        p_url = p.lower()        # "AOL.com" -> "aol.com"
        try:
            url = gusers.create_login_url(federated_identity=p_url)
            if not url:
                url = create_openid_url(p_url)
        except TypeError:
            continue
        #response.out.write('<b><i><a href="%s">%s</a></i><b> - ' % (url, p_name))
        urls[p_name] = url
    return urls

def logouturl(request, response):
    """ return google login url. """
    from google.appengine.api import users as gusers
    return gusers.create_logout_url(request.uri)

