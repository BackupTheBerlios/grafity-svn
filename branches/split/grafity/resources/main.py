#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.uic import Compiler

from grafity.base.items import Folder
from grafity.base.project import Project

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
        item = self._fromindex(parent)
        if isinstance(item, Folder):
            return len(list(item.contents()))
        else:
            return 0

    def data(self, index, role):
        obj = self._fromindex(index)
        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(obj.name)
        elif role == QtCore.Qt.DecorationRole:
            if isinstance(obj, Folder):
                icon = QtGui.QIcon('/home/daniel/grafity/grafity/resources/images/new/general/folder.png')
            else:
                icon = QtGui.QIcon('/home/daniel/grafity/grafity/resources/images/new/general/worksheet.png')
            return QtCore.QVariant(icon)
        else:
            return QtCore.QVariant()

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
            return self.project.top
        else:
            return self.project.store[self.ids[index.internalId()]]

    def parent(self, index):
        parent = self._fromindex(index).folder
        if parent == self.project.top:
            return QtCore.QModelIndex()
        return self.createIndex(list(parent.folder.contents()).index(parent), 0, self._getpos(parent.oid))

class MainWindow(QtGui.QMainWindow, Compiler.compileUiToType("main.ui")):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        self.setWindowFlags(self.windowFlags()&QtCore.Qt.Tool)
        self.setupUi(self)

        self.tree.header().hide()
        self.connect(self.tree, QtCore.SIGNAL('activated(QModelIndex)'), self.foo)



    def foo(self, *args):
        print >>sys.stderr, args
        p.new_folder('macaroni', f1)
        view.model().emit(QtCore.SIGNAL("layoutChanged()"))



if __name__ == "__main__":

    p = Project()
#    f1 = p.new_folder('foobar')
#    f2 = p.new_worksheet('bs5', f1)
#    f2 = p.new_folder('foobaassr', f1)
#    f2 = p.new_folder('foobaass2', f1)
#    f2 = p.new_folder('foobaass3', f1)
#    f2 = p.new_worksheet('bs1', f1)
#    f3 = p.new_worksheet('bs2', f1)
#    f3 = p.new_worksheet('bs3', f1)
#    f3 = p.new_folder('foobar2')
#    p.store.commit()

    app = QtGui.QApplication(sys.argv)
    form = MainWindow()
    form.show()
    m = TreeModel(p)
    form.tree.setModel(m)
    app.exec_()
