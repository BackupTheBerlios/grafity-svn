import sys


print >>sys.stderr, "import qt...",
from PyQt4.Qt import *
print >>sys.stderr, "ok"

print >>sys.stderr, "import grafity...",
from dispatch import dispatcher

from pkg_resources import resource_stream

from grafity.base.items import Folder
from grafity.base.graph import Graph
from grafity.base.worksheet import Worksheet
from grafity.base.project import Project
from grafity.ui.console import Console
from grafity.ui.properties import Properties
from grafity.ui.forms import qtresources

print >>sys.stderr, "ok"

import sip


class TreeModel(QAbstractItemModel):
    def __init__(self, project, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.project = project
        self.ids = {}
        
        dispatcher.connect(self.update, signal='added')

    def update(self, folder):
        print >>sys.stderr, 'update'
        self.emit(SIGNAL("layoutChanged()"))

    def headerData(self, section, orientation, role):
        return QVariant('section one')

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
        if role == Qt.DisplayRole:
            return QVariant(obj.name)
        elif role == Qt.DecorationRole:
            if isinstance(obj, Folder):
                icon = QIcon('/home/daniel/grafity/grafity/resources/images/new/general/folder.png')
            elif isinstance(obj, Graph):
                icon = QIcon('/home/daniel/grafity/grafity/resources/images/new/general/graph.png')
            else:
                icon = QIcon('/home/daniel/grafity/grafity/resources/images/new/general/worksheet.png')
            return QVariant(icon)
        else:
            return QVariant()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

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
            return QModelIndex()
        return self.createIndex(list(parent.folder.contents()).index(parent), 0, self._getpos(parent.oid))

from forms.main import Ui_MainWindow
#class MainWindow(formclass, baseclass):
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args):
#        QWidget.__init__(self, *args)
        QMainWindow.__init__(self, *args)
#        self.setWindowFlags(self.windowFlags()&Qt.Tool)
        self.setupUi(self)

        self.tree.header().hide()
        self.connect(self.tree, SIGNAL('activated(QModelIndex)'), self.foo)

        self.console = Console(self)
        self.properties = Properties(self)

    @pyqtSignature("")
    def on_action_New_activated(self):
        project = Project()
        f1 = project.new_folder('foobar')
        f2 = project.new_worksheet('bs5', f1)
        self.open_project(project)

    @pyqtSignature("")
    def on_action_Open_activated(self):
        filename = QFileDialog.getOpenFileName(self, "Choose a file", "", "Projects (*.grafity);;All files (*)")
        if filename is not None:
            self.open_project(Project(str(filename)))

    @pyqtSignature("")
    def on_actionE_xit_activated(self):
        sys.exit(0)

    @pyqtSignature("")
    def on_actionProperties_activated(self):
        if self.properties.isVisible():
            self.properties.raise_()
            self.properties.show()
        else:
            self.properties.show()


    @pyqtSignature("")
    def on_actionConsole_activated(self):
        if self.console.isVisible():
            self.console.raise_()
            self.console.show()
        else:
            self.console.show()

    @pyqtSignature("")
    def on_actionNew_Worksheet_activated(self):
        sheet = self.project.new_worksheet('sheet1')
        sheet.a = [1,2,3]
        sheet.b = [4,5,6]
        self.model.emit(SIGNAL("layoutChanged()"))

    @pyqtSignature("")
    def on_actionNew_Graph_activated(self):
        graph = self.project.new_graph('graph1')
        self.model.emit(SIGNAL("layoutChanged()"))

    def open_project(self, project):
        self.project = project
        self.console.text.locals['project'] = project
        self.console.text.locals['main'] = self
        self.model = TreeModel(self.project)
        self.tree.setModel(self.model)

    def foo(self, index):
        from worksheet import WorksheetView
#        from graph import GraphView
        obj = self.model._fromindex(index) 
        if isinstance(obj, Worksheet):
            view = WorksheetView(self, obj)
        elif isinstance(obj, Graph):
            view = GraphView(self, obj)
#        view = GraphView(self, None)
        view.show()
#        print >>sys.stderr, args
#        p.new_folder('macaroni', f1)


def main():
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
