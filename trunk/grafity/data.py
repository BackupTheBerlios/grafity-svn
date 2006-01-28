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

def scan_images():
    def walk_images(_, folder, files):
        for f in files:
            full = os.path.join(folder, f)
            if os.path.isfile(full) and fnmatch.fnmatch(f, "*.png"):
                images[f[:-4]] = full
    sys.stderr.write("scanning images...")
    os.path.walk(os.path.join(DATADIR, 'data'), walk_images, None)
    os.path.walk(USERDATADIR, walk_images, None)
    sys.stderr.write('%s loaded\n'%len(images))

def getimage(name, cache={}):
    if name not in cache:
        cache[name] = QPixmap(images[name])
    return cache[name]

scan_images()
scan_plugins()
