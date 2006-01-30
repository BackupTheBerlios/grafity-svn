import sys
import fnmatch
import os.path
from settings import USERDATADIR

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

def scan_functions_dir(functions, dirs):
    def walk_functions(functions, folder, files):
        for f in files:
            full = os.path.join(folder, f)
            if os.path.isfile(full) and fnmatch.fnmatch(f, "*.function"):
                functions.append((False, full))
    for dir in dirs:
        os.path.walk(dir, walk_functions, functions)

def scan_functions_resource(functions, start='data'):
    for name in resource_listdir('grafity', start):
        full = os.path.join(start, name)
        if resource_isdir('grafity', full):
            scan_functions_resource(functions, full)
        elif fnmatch.fnmatch(name, "*.function"):
            functions.append((True, full))

def scan_functions(dirs):
    functions = []
    scan_functions_dir(functions, dirs)
    scan_functions_resource(functions)
    return functions

def scan_plugins_dir():
    def walk_plugins(_, folder, files):
        for f in files:
            full = os.path.join(folder, f)
            if os.path.isfile(full) and fnmatch.fnmatch(f, "*.py"):
                execfile(full, {})
    os.path.walk(USERDATADIR, walk_plugins, None)

def scan_plugins_resource(start='data'):
    for name in resource_listdir('grafity', start):
        full = os.path.join(start, name)
        if resource_isdir('grafity', full):
            scan_plugins_resource(full)
        elif fnmatch.fnmatch(name, "*.py"):
            execfile(resource_filename('grafity', full), {})


images = {}

from pkg_resources import resource_isdir, resource_listdir, resource_filename

def scan_images_resource(start='data'):
    for name in resource_listdir('grafity', start):
        full = os.path.join(start, name)
        if resource_isdir('grafity', full):
            scan_images_resource(full)
        elif fnmatch.fnmatch(name, "*.png"):
            images[name[:-4]] = (True, full)

def scan_images_dir():
    def walk_images(_, folder, files):
        for f in files:
            full = os.path.join(folder, f)
            if os.path.isfile(full) and fnmatch.fnmatch(f, "*.png"):
                images[f[:-4]] = (False, full)
    os.path.walk(USERDATADIR, walk_images, None)

scan_images_resource()
scan_images_dir()
scan_plugins_resource()
scan_plugins_dir()
