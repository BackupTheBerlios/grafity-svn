import sys
import fnmatch
import os.path
from qt import QPixmap

def column_tool(name, image=None):
    def column_tool_dec(function):
        column_tools.append((name, function, image))
        return function
    return column_tool_dec

column_tools = []


def getimage(name, cache={}):
    if name not in cache:
        cache[name] = QPixmap(images[name])
    return cache[name]


def walk_data_dir((images, pyfiles, functions), folder, files):
    for f in files:
        full = os.path.join(folder, f)
        if os.path.isfile(full):
            if fnmatch.fnmatch(f, "*.png"):
                images[f[:-4]] = full
            elif fnmatch.fnmatch(f, "*.py"):
                pyfiles.append(full)
            elif fnmatch.fnmatch(f, "*.function"):
                functions.append(full)

images = {}
pyfiles = []
functions = []

sys.stderr.write("searching...")
os.path.walk('../data', walk_data_dir, (images, pyfiles, functions))
sys.stderr.write("%d images, %d scripts, %d fit functions loaded.\n" % (len(images), len(pyfiles), len(functions)))

for f in pyfiles:
    execfile(f, {})
