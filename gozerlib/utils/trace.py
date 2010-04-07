# gozerlib/utils/trace.py
#
#

""" trace related functions """

## basic imports

import sys
import os

## define

stopmarkers = ['gozerlib', 'commonplugs', 'waveplugs', 'socketplugs', 'waveapi', 'jsonbot']

## functions

def calledfrom(frame):
    """ return the plugin name where given frame occured. """
    try:
        filename = frame.f_back.f_code.co_filename
        plugfile = filename.split(os.sep)

        if plugfile:
            mod = []

            for i in plugfile[::-1]:
                mod.append(i)
                if i in stopmarkers:
                    break


            modstr = '.'.join(mod[::-1])[:-3]

            if 'handler_' in modstr:
                modstr = modstr.split('.')[-1]
        
    except AttributeError:
        modstr = None

    del frame
    return modstr

def callstack(frame):
    """ return callstack trace as a string. """
    result = []
    loopframe = frame

    while 1:
        try:
            filename = loopframe.f_back.f_code.co_filename
            result.append("%s:%s" % '.'.join((filename[:-3].split(os.sep)), loopframe.f_back.f_lineno))
            loopframe = loopframe.f_back
        except:
            break

    del frame
    return result

def whichmodule(depth=1):
    """ return filename:lineno of the module. """
    try:
        frame = sys._getframe(depth)
        plugfile = frame.f_back.f_code.co_filename[:-3].split('/')
        lineno = frame.f_back.f_lineno
        mod = []

        for i in plugfile[::-1]:
             mod.append(i)

             if i in stopmarkers:
                 break

        modstr = '.'.join(mod[::-1]) + ':' + str(lineno)

        if 'handler_' in modstr:
            modstr = modstr.split('.')[-1]

    except AttributeError:
        modstr = None

    del frame
    return modstr

def whichplugin(depth=1):
    """ return filename:lineno of the module. """
    try:
        frame = sys._getframe(depth)
        plugfile = frame.f_back.f_code.co_filename[:-3].split('/')
        lineno = frame.f_back.f_lineno
        mod = []

        for i in plugfile[::-1]:
             mod.append(i)

             if i in stopmarkers:
                 break

        modstr = '.'.join(mod[::-1])

        if 'handler_' in modstr:
            modstr = modstr.split('.')[-1]

    except AttributeError:
        modstr = None

    del frame
    return modstr
