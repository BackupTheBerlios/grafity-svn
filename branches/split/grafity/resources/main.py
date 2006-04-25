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

    @QtCore.pyqtSignature("")
    def on_action_New_activated(self):
        project = Project()
        f1 = project.new_folder('foobar')
        f2 = project.new_worksheet('bs5', f1)
        self.open_project(project)

    @QtCore.pyqtSignature("")
    def on_action_Open_activated(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Choose a file", "", "Projects (*.grafity);;All files (*)")
        if filename is not None:
            self.open_project(Project(str(filename)))

    @QtCore.pyqtSignature("")
    def on_actionE_xit_activated(self):
        sys.exit(0)

    @QtCore.pyqtSignature("")
    def on_actionNew_Worksheet_activated(self):
        sheet = self.project.new_worksheet('sheet1')
        sheet.a = [1,2,3]
        sheet.b = [4,5,6]
        self.model.emit(QtCore.SIGNAL("layoutChanged()"))

    def open_project(self, project):
        self.project = project
        self.model = TreeModel(self.project)
        self.tree.setModel(self.model)

    def foo(self, index):
        from worksheet import WorksheetView
        view = WorksheetView(self, self.model._fromindex(index))
        view.show()
#        print >>sys.stderr, args
#        p.new_folder('macaroni', f1)
#        view.model().emit(QtCore.SIGNAL("layoutChanged()"))


def main():
    app = QtGui.QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
