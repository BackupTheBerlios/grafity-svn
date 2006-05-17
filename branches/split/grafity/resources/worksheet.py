#!/usr/bin/env python
import sys

from PyQt4 import QtGui as qt
from PyQt4.QtCore import Qt
from PyQt4 import QtCore, uic

from grafity.base.arrays import nan

c1, c2 = uic.loadUiType("worksheet.ui")
class WorksheetView(c1, c2):
    def __init__(self, parent, worksheet):
        qt.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.worksheet = worksheet

        self.m = WorksheetModel(worksheet)
        self.table.setModel(self.m)

    @QtCore.pyqtSignature("")
    def on_actionNew_Column_activated(self):
        self.worksheet[self.worksheet.suggest_column_name()] = [1,2,3]
        self.table.model().emit(QtCore.SIGNAL('layoutChanged()'))

class WorksheetModel(QtCore.QAbstractTableModel):
    def __init__(self, worksheet):
        QtCore.QAbstractTableModel.__init__(self)
        self.worksheet = worksheet

    def rowCount(self, parent):
        return 10000

    def columnCount(self, parent):
        return len(self.worksheet.columns)

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        return QtCore.QVariant(str(self.worksheet[index.column()][index.row()]).replace(repr(nan), ''))

    def flags(self, index):
        return QtCore.QAbstractTableModel.flags(self, index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role):
        val = self.worksheet.evaluate(unicode(value.toString()))
        self.worksheet[index.column()][index.row()] = val
        self.emit(QtCore.SIGNAL('dataChanged()'))
        return True
