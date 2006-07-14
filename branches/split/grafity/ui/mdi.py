import sys


from PyQt4.Qt import *
from dispatch import dispatcher

dispatcher.send('splash-message', msg='Loading modules..,')
from pkg_resources import resource_stream
from grafity.base.items import Folder
from grafity.base.graph import Graph
from grafity.base.worksheet import Worksheet
from grafity.base.project import Project
from grafity.ui.console import Console
from grafity.ui.properties import Properties
from grafity.ui.forms import qtresources


class TreeModel(QAbstractItemModel):
    def __init__(self, project, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.project = project
        self.ids = {}
        
        dispatcher.connect(self.update, signal='added')
        dispatcher.connect(self.update, signal='removed')

    def update(self, folder=None):
        print >>sys.stderr, 'update', type(folder)
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
                icon = QIcon(':/images/general/folder.png')
            elif isinstance(obj, Graph):
                icon = QIcon(':/images/general/graph.png')
            else:
                icon = QIcon(':/images/general/worksheet.png')
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

from forms.mdi import Ui_MainWindow
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.setupUi(self)

        self.otoolbar = QToolBar(self)
        self.hboxlayout.addWidget(self.otoolbar)
        self.workspace = QWorkspace(self)
        self.hboxlayout.addWidget(self.workspace)

        self.toolBar.addSeparator()

        act = self.left.toggleViewAction()
        act.setIcon(QIcon(":/images/general/navigator.png"))
        self.toolBar.addAction(act)

        act = self.right.toggleViewAction()
        act.setIcon(QIcon(":/images/properties.png"))
        self.toolBar.addAction(act)

        self.bottomact = self.bottom.toggleViewAction()
        self.bottomact.setIcon(QIcon(":/images/general/script.png"))
        self.toolBar.addAction(self.bottomact)

        self.bottom.hide()
        self.right.hide()

        self.tree.header().hide()
        self.connect(self.tree, SIGNAL('activated(QModelIndex)'), self.foo)
#        self.insertToolBarBreak(self.toolbar2)

#        self.console = Console(self)
#        self.properties = Properties(self)

    @pyqtSignature("")
    def on_action_new_activated(self):
        project = Project()
        f1 = project.new_folder('foobar')
        f2 = project.new_worksheet('bs5', f1)
        self.open_project(project)

    @pyqtSignature("")
    def on_action_open_activated(self):
        filename = QFileDialog.getOpenFileName(self, "Choose a file", "", "Projects (*.grafity);;All files (*)")
        if filename is not None:
            self.open_project(Project(str(filename)))

    @pyqtSignature("")
    def on_actionE_xit_activated(self):
        self.close()

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
        self.project.store.begin('new worksheet')
        try:
            sheet = self.project.new_worksheet('sheet1')
            sheet.a = [1,2,3]
            sheet.b = [4,5,6]
        except:
#            st.rollback()
            raise
        else:
            self.project.store.commit()
#        self.model.emit(SIGNAL("layoutChanged()"))

    @pyqtSignature("")
    def on_actionNew_Graph_activated(self):
        self.project.store.begin('new graph')
        try:
            graph = self.project.new_graph('graph1')
        except:
            raise
        else:
            self.project.store.commit()
#        self.model.emit(SIGNAL("layoutChanged()"))

    def open_project(self, project):
        self.project = project
        self.console.locals['project'] = project
        self.console.locals['main'] = self
        self.model = TreeModel(self.project)
        self.tree.setModel(self.model)

    @pyqtSignature("")
    def on_action_Undo_activated(self):
        self.project.store.undo()

    @pyqtSignature("")
    def on_action_Redo_activated(self):
        self.project.store.redo()

    def foo(self, index):
        from worksheet import WorksheetView
        from graph import GraphView
        obj = self.model._fromindex(index) 
        if isinstance(obj, Worksheet):
            view = WorksheetView(self.workspace, obj)
            self.workspace.addWindow(view)
        elif isinstance(obj, Graph):
            view = GraphView(self.workspace, obj)
            self.workspace.addWindow(view)
#        view = GraphView(self, None)
        view.show()
#        print >>sys.stderr, args
#        p.new_folder('macaroni', f1)


def main():
    app = QApplication(sys.argv)
    pm = QPixmap("splash.png")
    splash = QSplashScreen(pm)
    splash.show()

    form = MainWindow()
    form.show()
    splash.finish(form)
    app.exec_()


if __name__ == "__main__":
    main()
