#!/usr/bin/env python
import sys

from PyQt4 import QtGui as qt
from PyQt4.QtCore import Qt
from PyQt4.uic import Compiler

app = qt.QApplication(sys.argv)
ui = Compiler.compileUiToType("graph_editor.ui")

class DemoImpl(qt.QDialog, ui):
    def __init__(self, *args):
        qt.QWidget.__init__(self, *args)
        self.setWindowFlags(self.windowFlags()&Qt.Tool)
        self.setupUi(self)
        self.tabs.setTabIcon(0, qt.QIcon('images/new/general/worksheet.png'))
        self.tabs.setTabIcon(1, qt.QIcon('images/new/general/style.png'))
        self.tabs.setTabIcon(2, qt.QIcon('images/16/axes.png'))
        self.tabs.setTabIcon(3, qt.QIcon('images/16/function.png'))
        self.tabnames = ['Data', 'Style', 'Axes', 'Fit']
    
    def on_tabs_currentChanged(self, i):
        if not isinstance(i, int):
            return
        for t in range(self.tabs.count()):
            self.tabs.setTabText(t, self.tabnames[t]*(i==t))

form = DemoImpl()
form.show()
app.exec_()
