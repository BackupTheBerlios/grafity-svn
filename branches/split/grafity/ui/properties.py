#!/usr/bin/env python
import sys

from pkg_resources import resource_stream

from PyQt4.Qt import *
from PyQt4 import uic

from grafity.ui.forms.properties import Ui_GraphEditor

class Properties(QDialog, Ui_GraphEditor):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)

