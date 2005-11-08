import sys
import os
import mingui as gui

sys.path.append("..")

from grafity.signals import HasSignals
from grafity import Project, Folder, Worksheet, Graph
from grafity.settings import settings, DATADIR
from grafity.arrays import nan
from grafity.actions import action_list, undo, redo

from ui_worksheet_view import WorksheetView
from ui_graph_view import GraphView, GraphDataPanel, GraphStylePanel

class ProjectShell(gui.PythonShell):
    """
    The shell window.

    All objects in the current folder are accesible, as well
    as the following objects:
        project - the current project
        here - the current folder
        this - the current object
        up - the parent folder
    """

    def setup(self):
        self.run('from grafity.arrays import *')
        self.run('from grafity import *')
        self.clear()
        self.run('print "# Welcome to Grafit"')
        self.prompt()

        mainwin = self.rfind('mainwin')
        mainwin.connect('open-project', self.on_open_project)
        mainwin.connect('close-project', self.on_close_project)

    def on_open_project(self, project):
        """called when a new project is opened"""
        self.locals.update({'project': project})
        self.run('project.set_dict(globals())')

    def on_close_project(self, project):
        """called when the project is closed"""
        self.locals['project'].unset_dict()
        self.locals.update({'project':None})


class FolderListData(HasSignals):
    def __init__(self, folder):
        self.folder = folder
        self.update()
        self.folder.connect('modified', self.update)

    def update(self):
        self.contents = [self.folder.parent]*(self.folder!=self.folder.project.top) + \
                        list(self.folder.contents())
        self.emit('modified')

    def get(self, row, column):
        if self.contents[row] == self.folder.parent: return '../'
        return self.contents[row].name + '/'*isinstance(self.contents[row], Folder)

    def get_image(self, row):
        obj = self.contents[row]
        if isinstance(obj, Worksheet): return 'worksheet'
        elif isinstance(obj, Graph): return 'graph'
#        elif isinstance(obj, Folder): return ['folder_new', 'uptriangle-o'][obj == self.folder.parent]

    def __len__(self): return len(self.contents)

    def __getitem__(self, row): return self.contents[row]


class FolderBrowser(gui.List):
    def setup(self):
        self.rfind('mainwin').connect('open-project', self.on_open_project)
        self.rfind('mainwin').connect('close-project', self.on_close_project)

        self.connect('item-activated', self.on_activated)

    def on_open_project(self, project):
        project.connect('change-current-folder', self.cd)

    def on_close_project(self, project):
        project.disconnect('change-current-folder', self.cd)

    def on_activated(self, obj):
        if isinstance(obj, Folder):
            obj.project.cd(obj)
        elif isinstance(obj, Worksheet):
            gui.xml.build('worksheet-view',
                          place=gui.app.mainwin.book(label=obj.name), 
                          worksheet=obj,
                          src=globals())
        elif isinstance(obj, Graph):
            gui.xml.build('graph-view',
                          place=gui.app.mainwin.book(label=obj.name), 
                          graph=obj,
                          src=globals())

    def cd(self, folder):
        self.data = FolderListData(folder)


class ProjectTreeData(HasSignals):
    def __init__(self, project):
        self.project = project
        self.project.top.connect('modified', self.emitter('modified', self.project.top), True)

    def root(self):
        """Returns the object represented by the root node"""
        return self.project.top

    def children(self, obj):
        """Returns the children of object `obj`"""
        return obj.subfolders()

    def text(self, obj):
        """Returns the string representation of object `obj` in the tree"""
        return obj.name

    def image(self, obj):
        """Returns the image of object `obj` in the tree"""
        return None

    def rename(self, obj, newame):
        if newname == '':
            return False
        else:
            obj.name = newname.encode('utf-8')
            self.emit('modified', self.project.top)
            return True

    # signal 'modified' (obj)
    #   signals that the object `obj` has been modified and the 
    #   tree branch should be updated. If obj is None the whole
    #   tree should be updated.


class ProjectTree(gui.Tree):
    def setup(self):
        self.rfind('mainwin').connect('open-project', self.on_open_project)
        self.rfind('mainwin').connect('close-project', self.on_close_project)

        self.connect('selected', self.on_select)

    def on_open_project(self, project):
        self.set_data(ProjectTreeData(project))
        project.connect('change-current-folder', self.on_change_folder)

    def on_close_project(self, project):
        self.clear()
        project.disconnect('change-current-folder', self.on_change_folder)

    def on_select(self, item):
        item.project.cd(item)

    def on_change_folder(self, folder):
        self.select(folder, skip_event=True)


class MainWindow(gui.Window):
    def setup(self):
        self.book = self.find('notebook')
        self.tree = self.find('tree')
        self.shell = self.find('shell')
        self.list = self.find('lili')

        for cmd, method in {
            'file-open': self.on_open_project,
            'file-new': self.on_new_project,
            'file-save': self.on_save_project,
            'file-saveas': self.on_save_project_as, 
            'new-folder': self.on_new_folder, 
            'new-worksheet': self.on_new_worksheet, 
            'new-graph': self.on_new_graph, 
        }.iteritems():
            gui.commands[cmd].connect('activated', method)
            
        self.find('projectpane').parent.open(self.find('projectpane'))

        self.open_project(Project())


    def open_project(self, project):
        """Open a project in the main window"""
        self.project = project

        self.project.connect('remove-item', self.on_project_remove_item)
        self.project.connect('modified', lambda: self.on_project_modified(True), True)
        self.project.connect('not-modified', lambda: self.on_project_modified(False), True)

        action_list.clear()

        self.emit('open-project', self.project)

    def can_close_project(self):
        """Return whether we are allowed to close the current project.
        Asks the user whether to save changes and saves, when appropriate
        """
        if self.project is not None:
            if self.project.modified:
                result = gui.alert_yesnocancel('Save changes to this project?', 'Save?')
                if result == 'yes':
                    sresult = self.on_save_project()
                    if not sresult:
                        return False
                elif result == 'cancel':
                    return False
        return True

    def close_project(self):
        """Close the active project and clear appropriate windows"""
        self.project.disconnect('remove-item', self.on_project_remove_item)

        for signal in ['modified', 'not-modified']:
            for slot in self.project._signals[signal]:
                self.project.disconnect(signal, slot)

        self.emit('close-project', self.project)
        self.project = None


    # Handle commands

    def on_new_project(self):
        if self.can_close_project():
            self.open_project(Project())

    def on_open_project(self):
        if self.can_close_project():
            files = gui.request_file_open(wildcard="All Files|*.*|Projects|*.gt")
            if files is not None:
                if self.can_close_project():
                    self.close_project()
                    self.open_project(Project(files[0]))

    def on_save_project(self):
        if self.project.filename is not None:
            self.project.commit()
            return True
        else:
            return self.on_save_project_as()

    def on_save_project_as(self):
        fil = gui.request_file_save(wildcard="All Files|*.*|Projects|*.gt")
        if fil is not None:
            self.project.saveto(fil)
            self.close_project()
            self.open_project(Project(fil))
            return True
        else:
            return False

    def on_new_graph(self):
        g = self.project.new(Graph, None, self.project.here)

    def on_new_folder(self):
        self.project.new(Folder, None, self.project.here)

    def on_new_worksheet(self):
        ws = self.project.new(Worksheet, None, self.project.here)
        ws.a = [nan]*100
        ws.b = [nan]*100


    # Handle events

    def on_project_modified(self, mod):
        gui.commands['file-save'].enabled = mod

    def on_project_remove_item(self, item):
        pass


def main():
    gui.xml.merge('grafity.ui')
    gui.run(gui.xml.build('mainwin', src=globals()))

if __name__ == '__main__':
    main()
