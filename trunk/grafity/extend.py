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

def extension(extname):
    return extension_types[extname]

def options(**kwds):
    def dec(func):
        for key, value in kwds.iteritems():
            setattr(func, key, value)
        return func
    return dec


column_tools = []

@extension_type('column-tool')
def column_tool_dec(function):
    print >>sys.stderr, "registering column tool", function.name
    if hasattr(function, 'image'):
        img = function.image
    else:
        img = None
    column_tools.append((function.name, function, img))
    return function


def dataset_tool(name, image=None):
    def dataset_tool_dec(function):
        dataset_tools.append((name, function, image))
        return function
    return dataset_tool_dec

dataset_tools = []

def register_graph_mode(mode):
    print >>sys.stderr, "registering graph mode", mode.name
    graph_modes.append(mode)

graph_modes = []


