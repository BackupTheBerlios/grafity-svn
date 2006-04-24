#!/usr/bin/env python
import sys

from PyQt4 import QtGui as qt
from PyQt4.QtCore import Qt
from PyQt4 import QtCore
from PyQt4.uic import Compiler

ui = Compiler.compileUiToType("worksheet.ui")
class WorksheetView(qt.QMainWindow, ui):
    def __init__(self, parent, worksheet):
        qt.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.worksheet = worksheet

        self.m = WorksheetModel(worksheet)
        self.table.setModel(self.m)

class WorksheetModel(QtCore.QAbstractTableModel):
    def __init__(self, worksheet):
        QtCore.QAbstractTableModel.__init__(self)
        self.worksheet = worksheet

    def rowCount(self, parent):
        return 150000

    def columnCount(self, parent):
        return len(self.worksheet.columns)

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        return QtCore.QVariant(str(self.worksheet[index.column()][index.row()]))
