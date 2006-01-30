import sys
import fnmatch
import os.path
from settings import DATADIR, USERDATADIR
from qt import QPixmap

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

def scan_functions(dirs):
    functions = []
    def walk_functions(functions, folder, files):
        for f in files:
            full = os.path.join(folder, f)
            if os.path.isfile(full) and fnmatch.fnmatch(f, "*.function"):
                functions.append(full)
    for dir in dirs:
        os.path.walk(dir, walk_functions, functions)
    return functions

def scan_plugins():
    def walk_plugins(_, folder, files):
        for f in files:
            full = os.path.join(folder, f)
            if os.path.isfile(full) and fnmatch.fnmatch(f, "*.py"):
                execfile(full, {})
    os.path.walk(os.path.join(DATADIR, 'data'), walk_plugins, None)
    os.path.walk(USERDATADIR, walk_plugins, None)

images = {}

from pkg_resources import resource_isdir, resource_listdir, resource_filename

def scan_images(start=''):
    for name in resource_listdir('grafity', start):
        full = os.path.join(start, name)
        if resource_isdir('grafity', full):
            scan_images(full)
        if fnmatch.fnmatch(name, "*.png"):
            images[name[:-4]] = full

def getimage(name, cache={}):
    if name not in cache:
        cache[name] = QPixmap(resource_filename('grafity', images[name]))
        print >>sys.stderr, name
    return cache[name]


scan_images()
scan_plugins()
