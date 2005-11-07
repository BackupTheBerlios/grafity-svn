# setup.py
from distutils.core import setup
import py2exe

setup(
    options = {"py2exe": {"compressed": 1,
                          "optimize": 2,
                          "ascii": 1,
                          "bundle_files": 1}},
    zipfile = None,
    windows = ['detafix.py'],
    )