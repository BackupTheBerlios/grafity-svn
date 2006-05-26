#!/usr/bin/env python
import sys

from pkg_resources import resource_filename

from PyQt4.Qt import *
from PyQt4 import uic
from PyQt4 import Qwt5 as qwt

c1, c2 = uic.loadUiType(resource_filename('grafity', 'resources/ui/properties.ui'))
class Properties(c1, c2):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setupUi(self)

