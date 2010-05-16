# gozerlib/eggs.py
#
#

""" 

    eggs related functions

    this module is used to load the eggs on which gozerlib depends from 
    specified dir .. most of the time this is the jsbnest dir.

"""

## gozerlib imports

from utils.exception import handle_exception
from gozerlib.config import cfg as config

## basic imports

import os
import sys
import logging

## define

mainenv = None

## functions

def init(eggdir, log=True):

    """
        make sure setuptools is available.

        :param eggdir: directory to scan for eggs
        :type eggdir: string
        :param log: whether to log the registration of the setuptools egg
        :type log: True or False

    """
    try:
        import setuptools
    except ImportError, ex:
        try:
            sys.path.insert(0, eggdir)
            for egg in os.listdir(eggdir):
                if not egg.startswith('setuptools'):
                    log and logging.warn('eggs - loaded %s' % egg)
                    sys.path.insert(0, eggdir + os.sep + egg)
        except OSError:
            pass

latest = {}
    
def enable_egg(env, egg, log=True):
    """
        search for the latest version of an  egg in the enviroment and put 
        it on sys.path.

        :param env: the environment to search the egg in
        :type env: pkg_resources.Environment
        :param egg: egg to load or find a newer version for
        :param log: determine if we should log the enabling of the egg

    """
    try:
        from pkg_resources import DistributionNotFound, VersionConflict, working_set, parse_requirements, require
         
        if not latest.has_key(egg.project_name):
            latest[egg.project_name] = egg

        req = egg.as_requirement()
        reqstr = str(req)
        reqq = parse_requirements([reqstr.replace('==', '>='), ])
        for e in working_set.resolve(reqq, mainenv):
            if e.location not in sys.path:
                env.add(e)
                working_set.add(e)
                working_set.add_entry(e.location)
                latest[egg.project_name] = e
                sys.path.insert(0, egg.location)
                log and logging.warn('eggs - loaded %s' % e)
            else:
                log and logging.warn('eggs - %s already on path' % e)
    except DistributionNotFound, ex:
        env.add(egg)
        working_set.add(egg)
        working_set.add_entry(egg.location)
        latest[egg.project_name] = egg
        sys.path.insert(0, egg.location)
        log and logging('eggs - loaded %s' % egg)
    except VersionConflict, ex:
        if egg > ex[0]:
            env.add(egg)
            working_set.add_entry(egg.location)
            working_set.add(egg)
            latest[egg.project_name] = egg
            sys.path.insert(0, egg.location)
            log and logging.warn('eggs - override %s' % egg)

def loadegg(name, eggdirs=['jsbnest',], log=True):
    """
        scan eggdir for a egg matching `name`.

        :param name: piece of txt which should be in the egg projectname
        :type name: string
        :param eggdirs: directories to search in
        :type eggdirs: list
        :param log: boolean which indicates whether loading should be logged
        :type log: boolean

    """
    try:
        from pkg_resources import find_distributions, Environment
        global mainenv

        for eggdir in eggdirs:
            if mainenv:
                mainenv += Environment(eggdir)
            else:
                mainenv = Environment(eggdir)
            eggs = find_distributions(eggdir)
            for egg in eggs:
               if name.lower() in egg.project_name.lower():
                    enable_egg(mainenv, egg, log)

    except ImportError: 
        return
    except Exception, ex:
        handle_exception()

def loadeggs(eggdir, log=True):
    """
        load all eggs in a directory.

        :param eggdir: directory to load eggs from
        :type eggdir: string

    """
    logging.warn('eggs - scanning %s' % eggdir)
    try:
        from pkg_resources import find_distributions, Environment
        global mainenv

        if mainenv:
            mainenv += Environment(eggdir)
        else:
            mainenv = Environment(eggdir)
        eggs = find_distributions(eggdir)
        for egg in eggs:
            if not egg.project_name.startswith('setuptools'):
                enable_egg(mainenv, egg, log)

    except ImportError:
        return
    except Exception, ex:
        handle_exception()

    res = []
    for name, egg in latest.iteritems():
        res.append("%s: %s" % (name, egg.version))

    logging.warn('eggs - loaded: %s' % ' .. '.join(res))



## initialisation

try:
    import google
except ImportError:
    # first search for setuptools and load it
    init(os.getcwd())
    init(os.getcwd() + os.sep + 'jsbnest')
