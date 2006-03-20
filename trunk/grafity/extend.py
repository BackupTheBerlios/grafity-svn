"""
grafity.extend
"""
__author__ = "Daniel Fragiadakis <dfragi@gmail.com>"
__revision__ = "$Id$"

extension_types = {}

def extension_type(extname):
    return lambda func: extension_types.__setitem__(extname, func)

def extension(extname):
    return extension_types[extname]

def options(**kwds):
    def dec(func):
        for key, value in kwds.iteritems():
            setattr(func, key, value)
        return func
    return dec


