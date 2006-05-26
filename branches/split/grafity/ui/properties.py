#!/usr/bin/env python
import sys

from pkg_resources import resource_stream

from PyQt4.Qt import *
from PyQt4 import uic

c1, c2 = uic.loadUiType(resource_stream('grafity', 'resources/ui/properties.ui'))
class Properties(c1, c2):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setupUi(self)

