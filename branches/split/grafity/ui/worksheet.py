#!/usr/bin/env python
import sys

from PyQt4.Qt import *
from PyQt4 import uic

from grafity.base.arrays import nan
from grafity.ui.forms.worksheet import Ui_form
from pkg_resources import resource_stream

class WorksheetView(QWidget, Ui_form):
    def __init__(self, parent, worksheet):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.worksheet = worksheet

        self.m = WorksheetModel(worksheet)
        self.table.setModel(self.m)
#        self.table.verticalHeader().resizeSection(0, 10)
#        self.table.setRowHeight(8, 20)

        self.actions = [self.act_new_column, self.act_del_column, self.act_move_left]

    @pyqtSignature("")
    def on_act_new_column_activated(self):
        self.worksheet[self.worksheet.suggest_column_name()] = [1,2,3]
        self.table.model().emit(SIGNAL('layoutChanged()'))

class WorksheetModel(QAbstractTableModel):
    def __init__(self, worksheet):
        QAbstractTableModel.__init__(self)
        self.worksheet = worksheet

    def rowCount(self, parent):
        return 10000

    def columnCount(self, parent):
        return len(self.worksheet.columns)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()

        return QVariant(str(self.worksheet[index.column()][index.row()]).replace(repr(nan), ''))

    def flags(self, index):
        return QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable

    def setData(self, index, value, role):
        val = self.worksheet.evaluate(unicode(value.toString()))
        self.worksheet._project.store.begin('change-data')
        self.worksheet[index.column()][index.row()] = val
        self.worksheet._project.store.commit()
        self.emit(SIGNAL('dataChanged()'))
        return True
