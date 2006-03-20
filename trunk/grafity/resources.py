"""
grafity.resources
"""
__author__ = "Daniel Fragiadakis <dfragi@gmail.com>"
__revision__ = "$Id$"

import fnmatch
import os.path
import zipfile
import sys
from grafity.settings import USERDATADIR
import pkg_resources

def column_tool(name, image=None):
    def column_tool_dec(function):
        column_tools.append((name, function, image))
        return function
    return column_tool_dec

column_tools = []

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

processors = []

def processes_resource(pattern):
    def pres(fcn):
        processors.append((pattern, fcn))
    return pres

@processes_resource('*.png')
def process_image(res):
    images[os.path.splitext(os.path.basename(res))[0]] = res

@processes_resource('*.py')
def process_script(res):
    exec resource_data(res)

#@processes_resource('*.function')
def process_function(res):
    functions.append(res)

def scan_functions(dirs):
    functions = []
    scan_functions_dir(functions, dirs)
    scan_functions_resource(functions)
    return functions

def resource_data(res):
    protocol, path = res.split(':')
    if protocol == 'file':
        if '|' in path:
            zipname, zippath = path.split('|')
            zip = zipfile.ZipFile(zipname)
            return zip.read(zippath)
        else:
            return open(path).read()
    elif protocol == 'resource':
        if '|' in path:
            zipname, zippath = path.split('|')
            zip = zipfile.ZipFile(pkg_resources.resource_stream('grafity', zipname))
            return zip.read(zippath)
        else:
            return pkg_resources.resource_string('grafity', path)
    else:
        raise ValueError, "Unknown protocol: %s" % protocol

def resource_isdir(res):
    protocol, path = res.split(':')
    if protocol == 'file':
        return os.path.isdir(path) or path.endswith('.zip')
    elif protocol == 'resource':
        return pkg_resources.resource_isdir('grafity', path) or path.endswith('zip')

def resource_children(res):
    protocol, path = res.split(':')
    if protocol == 'file':
        if os.path.isdir(path):
            return ['file:'+os.path.join(path, f) for f in os.listdir(path)]
        elif path.endswith('.zip'):
            zip = zipfile.ZipFile(path)
            return ['file:'+path+'|'+f for f in zip.namelist()]
    elif protocol == 'resource':
        if pkg_resources.resource_isdir('grafity', path):
            return ['resource:'+os.path.join(path, f) 
                            for f in pkg_resources.resource_listdir('grafity', path)]
        elif path.endswith('.zip'):
            zip = zipfile.ZipFile(pkg_resources.resource_stream('grafity', path))
            return ['resource:'+path+'|'+f for f in zip.namelist()]


def resource_walk(res):
    if resource_isdir(res):
        for child in resource_children(res):
            for r in resource_walk(child):
                yield r
    else:
        yield res

def resource_process(res):
    for pattern, function in processors:
        if fnmatch.fnmatch(os.path.basename(r), pattern):
            function(r)

images = {}

def resource_search(pattern):
    for start in start_res:
        for res in resource_walk(start):
            if fnmatch.fnmatch(res, pattern):
                yield res

start_res = [ 'resource:resources', 'file:%s'%USERDATADIR ]

for start in start_res:
    for start in start_res:
        for res in resource_walk(start):
            resource_process(res)
