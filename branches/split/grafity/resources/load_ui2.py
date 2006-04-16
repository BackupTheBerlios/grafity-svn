#!/usr/bin/env python
import sys

from PyQt4 import QtGui
from PyQt4.uic import Loader

class DemoImpl(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        Loader.loadUi("graph_editor.ui", self)

    def on_button1_clicked(self):
        for s in "This is a demo".split(" "):
            self.list.addItem(s)

app = QtGui.QApplication(sys.argv)
widget = DemoImpl()
widget.show()
app.exec_()
