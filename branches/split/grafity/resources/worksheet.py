#!/usr/bin/env python
import sys

from PyQt4 import QtGui as qt
from PyQt4.QtCore import Qt
from PyQt4 import QtCore
from PyQt4.uic import Compiler

app = qt.QApplication(sys.argv)
ui = Compiler.compileUiToType("worksheet.ui")

class DemoImpl(qt.QDialog, ui):
    def __init__(self, *args):
        qt.QWidget.__init__(self, *args)
        self.setWindowFlags(self.windowFlags()&Qt.Tool)
        self.setupUi(self)
    

class ImageModel(QtCore.QAbstractTableModel):
#    def __init__(self, image, parent=None):
#        QtCore.QAbstractTableModel.__init__(self, parent)

    def rowCount(self, parent):
        return 150000

    def columnCount(self, parent):
        return 15

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        return QtCore.QVariant(str(index.column())+'.'+str(index.row()))

form = DemoImpl()
form.show()
m = ImageModel()
form.table.setModel(m)
app.exec_()
