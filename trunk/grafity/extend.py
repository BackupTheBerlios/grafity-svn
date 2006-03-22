"""
grafity.extend
"""
__author__ = "Daniel Fragiadakis <dfragi@gmail.com>"
__revision__ = "$Id$"


import sys

extension_types = {}

def extension_type(extname):
    def foo(func):
        print >>sys.stderr, "EXTENSION TYPE: '%s' registered" % extname
        extension_types[extname] = func
        return func
    return foo

def extension(extname, arg=None):
    if arg is None:
        return extension_types[extname]
    else:
        return extension_types[extname](arg)

def options(**kwds):
    def dec(func):
        for key, value in kwds.iteritems():
            setattr(func, key, value)
        return func
    return dec


