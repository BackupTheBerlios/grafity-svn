# setup.py
from distutils.core import setup
import py2exe

import sys

sys.path.append('..')

setup(
    options = {"py2exe": {"compressed": 1,
                          "optimize": 2,
                          "ascii": 1,
                          "bundle_files": 1}},
    zipfile = None,
    windows = ['../grafit/main.py'],
    )
