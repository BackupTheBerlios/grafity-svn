#!/usr/bin/env python

import sys
from PyQt4 import QtCore, QtGui


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, data, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)
        self.project = data
        self.ids = {}

    def headerData(self, section, orientation, role):
        return QtCore.QVariant('section one')

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        parent_item = self._fromindex(parent)
        return len(list(parent_item.contents()))

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        index_item = self._fromindex(index)

        return QtCore.QVariant(index_item.name)

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def index(self, row, column, parent):
        parent_item = self._fromindex(parent)
        oid = list(parent_item.contents())[row].oid
        return self.createIndex(row, column, self._getpos(oid))

    def _getpos(self, oid):
        if oid in self.ids.values():
            return [k for k, v in self.ids.iteritems() if v == oid][0]
        else:
            pos = len(self.ids)
            self.ids[pos] = oid
            return pos

    def _fromindex(self, index):
        if not index.isValid():
            obj = self.project.top
        else:
            obj = self.project.store[self.ids[index.internalId()]]

        return obj

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        parent = self.project.store[self.ids[index.internalId()]].folder
        if parent == self.project.top:
            return QtCore.QModelIndex()
        row = list(parent.folder.contents()).index(parent)
        return self.createIndex(row, 0, self._getpos(parent.oid))


def foo(*args):
    print >>sys.stderr, args
    p.new_folder('macaroni', f2)
    view.model().emit(QtCore.SIGNAL("layoutChanged()"))

from grafity.base.project import Project

if __name__ == "__main__":

    p = Project()
    f1 = p.new_folder('foobar')
    f2 = p.new_folder('foobaassr', f1)
    f2 = p.new_folder('foobaass2', f1)
    f2 = p.new_folder('foobaass3', f1)
    f3 = p.new_folder('foobar2')

    app = QtGui.QApplication(sys.argv)
    model = TreeModel(p)

    view = QtGui.QTreeView()
    view.connect(view, QtCore.SIGNAL("activated(const QModelIndex &)"), foo)
    view.setModel(model)
    view.setWindowTitle("Simple Tree Model")
    view.show()
    sys.exit(app.exec_())
