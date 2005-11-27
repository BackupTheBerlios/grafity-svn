import os
import tempfile
import subprocess
import sys

from grafity import Graph, Worksheet, Folder, Project
from grafity.ui_worksheet_view import WorksheetView
from grafity.ui_graph_view import GraphView
from grafity.import_ascii import import_ascii
from grafity.arrays import nan
from grafity.signals import HasSignals, global_connect
from grafity.actions import action_list, undo, redo
from grafity.settings import settings, DATADIR
from mingui import Window, Button, Box, Application, Shell, List, \
                       Splitter, Label, Tree, TreeNode, Notebook, MainPanel, \
                       OpenGLWidget, Table, Command, Menu, Menubar, Toolbar, Html
import grafity.signals

import wx
import wx.xrc

class ItemDragData(object):
    def __init__(self, items):
        self.items = items
        if Folder in [type(item) for item in items]:
            self.supported_formats = ['grafity-object']
        else:
            self.supported_formats = ['grafity-object', 'filename']

    def get_data(self, format):
        if format == 'grafity-object':
            return '\n'.join(i.id for i in self.items)
        elif format == 'filename':
            r = []
            for item in self.items:
                if isinstance(item, Worksheet):
                    filename = item.name + '.txt'
                elif isinstance(item, Graph):
                    filename = item.name + '.eps'
                elif isinstance(item, Folder):
                    filename = item.name
                d = tempfile.mkdtemp()
                f = open(d+'/'+filename, 'wb')
                if isinstance(item, Worksheet) or isinstance(item, Graph):
                    item.export_ascii(f)
                f.close()
                r.append(d+'/'+filename)
            return r

class Cancel(Exception):
    pass


class ScriptWindow(Shell):#, Pyro.core.ObjBase):
    def __init__(self, parent, **kwds):
        self.locals = {}
        Shell.__init__(self, parent, locals=self.locals, **kwds)

        self.run('from grafity.arrays import *')
        self.run('from grafity import *')

        self.clear()
        self.run('print "# Welcome to Grafit"')
        self.prompt()

    def connect_project(self, project):
        self.project = project
        self.locals.update({'project': project})
        self.run('project.set_dict(globals())')

    def disconnect_project(self):
        self.locals.update({'project': None})
        self.project.unset_dict()
        self.project = None


class FolderTreeNode(HasSignals):
    """Adapter from a folder to a Tree node"""
    def __new__(cls, folder, **kwds):
        if hasattr(folder, '_treenode'):
            return folder._treenode
        else:
            obj = HasSignals.__new__(cls, folder, **kwds)
            folder._treenode = obj
            return obj

    def __init__(self, folder, isroot=False):
        self.folder = folder
        self.folder.connect('modified', self.on_modified)
        if isroot:
            self.folder.project.connect('add-item', self.on_modified)
            self.folder.project.connect('remove-item', self.on_modified)
        self.subfolders = list(self.folder.subfolders())

    def __iter__(self):
        for item in self.folder.contents():
            if isinstance(item, Folder):
                yield FolderTreeNode(item)
    
    def __str__(self): 
        return self.folder.name.decode('utf-8')

    def get_pixmap(self): 
#        if self.folder == self.folder.project.top:
#            return 'grafity16.png'
#        else:
            return '16/folder.png'

    def on_modified(self, item=None): 
        subfolders = list(self.folder.subfolders())
        if subfolders != self.subfolders:
            self.emit('modified')
            self.subfolders = subfolders

    def rename(self, newname):
        if newname == '':
            return False
        else:
            self.folder.name = newname.encode('utf-8')
            self.folder.project.top.emit('modified')
            return True

#    def close(self):
#        print >>sys.stderr, 'close'
#    def open(self):
#        print >>sys.stderr, 'open'

class ProjectExplorer(Box):
    def __init__(self, parent, **kwds):
        Box.__init__(self, parent, 'horizontal', **kwds)
        self.splitter = Splitter(self, 'horizontal')

        self.tree = Tree(self.splitter)
        self.tree.enable_drop(['grafity-object'])

        self.tree.connect('drop-hover', self.on_drop_hover)
        self.tree.connect('drop-ask', self.on_tree_drop_ask)
        self.tree.connect('dropped', self.on_tree_dropped)

        self.tree.connect('selected', self.on_tree_selected)

        self.list = List(self.splitter, editable=True)
        self.list.enable_drop(['grafity-object', 'filename'])

        self.list.connect('drop-hover', self.on_drop_hover)
        self.list.connect('dropped', self.on_dropped)
        self.list.connect('drop-ask', self.on_drop_ask)

        self.list.connect('drag-begin', self.on_begin_drag)

        self.list.connect('item-activated', self.on_list_item_activated)
        self.list.connect('right-click', self.on_list_right_click)

        self.list.connect('end-edit', self.on_item_edited)

    def on_item_edited(self, item, str):
        item = self.list.model[item]
        item.name = str
        return True

    def on_list_right_click(self, item):
        if item == -1:
            return
        item = self.list.model[item]
        menu = Menu()
        menu.append(Command('Delete', 'delete', object, 'stock_delete.png'))
        menu.append(None)
        menu.append(Command('Preview PostScript', 'Preview PostScript', 
                    lambda: self.on_preview_ps(item), 'stock_print-preview.png'))
        menu.append(Command('Export...', 'Export', object, 'stock_export.png'))
        self.list._widget.PopupMenu(menu._menu)


    def on_tree_drop_ask(self, item):
        return True

    def on_preview_ps(self, item):
        d = tempfile.mkdtemp()
        f = open(d+'/preview.eps', 'wb')
        item.export_ascii(f)
        f.close()
        subprocess.Popen(['evince', d+'/preview.eps'])

    def on_tree_dropped(self, item, data):
        if 'grafity-object' in data.formats:
            for d in data.get('grafity-object').split('\n'):
                self.project.items[d].parent = item.folder
            return True
        else:
            return False

    def on_drop_hover(self, item):
#        if item != -1:
            return 'copy'

    def on_drop_ask(self, item):
        if item != -1 and isinstance(self.list.model[item], Folder):
            return True
        else:
            return True
#            return False

    def on_dropped(self, item, data):
        if 'grafity-object' in data.formats:
            parent = self.list.model[item]
            for d in data.get('grafity-object').split('\n'):
                self.project.items[d].parent = parent
            return True
        elif 'filename' in data.formats and item == -1:
            # import ascii
            for path in data.get('filename'):
                ws = self.project.new(Worksheet, str(os.path.basename(path).split('.')[0]), self.project.here)
                ws.array, ws._header = import_ascii(path)
            return False
        else:
            return False
#        else:
#            print 'DROPPED: ', format, data

    def on_begin_drag(self, item):
        return ItemDragData([self.list.model[i] for i in self.list.selection])

    def on_tree_selected(self, item):
        self.list.model = FolderListData(item.folder)
        self.project.cd(item.folder)

    def on_list_item_activated(self, item):
        obj = self.list.model[item]
        if isinstance(obj, Folder):
            self.list.model = FolderListData(obj)
            self.project.cd(obj)
        else:
            self.emit('item-activated', obj)

    def connect_project(self, project):
        self.project = project
        root = FolderTreeNode(self.project.top, isroot=True)
        self.tree.append(root)
        self.on_tree_selected(root)

    def disconnect_project(self):
        self.project = None
        self.tree.clear()

class ActionListModel(HasSignals):
    def __init__(self, actionlist):
        self.actionlist = actionlist
        self.actionlist.connect('added', self.on_modified)
        self.actionlist.connect('removed', self.on_modified)
        self.actionlist.connect('modified', self.on_modified)

    def on_modified(self, action=None):
        self.emit('modified')
        
    # list model interface
    def get(self, row, column): 
        com = self.actionlist.actions[row]
        if com.done:
            return str(com)
        else:
            return '('+str(com)+')'
    def get_image(self, row): 
        com = self.actionlist.actions[row]
        if com.done:
            return 'command-done.png'
        else:
            return 'command-undone.png'
    def __len__(self): return len(self.actionlist.actions)

class ActionList(Box):
    def __init__(self, actionlist, parent, **place):
        Box.__init__(self, parent, 'vertical', **place)
        self.list = List(self, model=ActionListModel(actionlist), stretch=1.)
        self.list._widget.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.list.connect('item-activated', self.on_list_item_activated)
        self.list.connect('selection-changed', self.on_list_selection_changed)
#        self.label = Label(self, 'Action', stretch=0.)
        self.label = Html(self, stretch=.5)

    def on_list_item_activated(self, idx):
        com = self.list.model.actionlist.actions[idx]
        if com.done:
            while com.done:
                undo()
        else:
            while not com.done:
                redo()

    def on_list_selection_changed(self):
        com = self.list.model.actionlist.actions[self.list.selection[0]]
        text = "<html><body><i>"+str(com)+"</i></body></html>"
#        self.label.text = str(com)
        self.label._widget.SetStandardFonts()
        self.label._widget.SetPage(text)

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
        if self.contents[row] == self.folder.parent:
            return '../'
        return self.contents[row].name + '/'*isinstance(self.contents[row], Folder)
    def get_image(self, row):
        obj = self.contents[row]
        if isinstance(obj, Worksheet):
            return 'worksheet.png'
        elif isinstance(obj, Graph):
            return 'graph.png'
        elif isinstance(obj, Folder):
            return ['16/folder.png', '16/up.png'][obj == self.folder.parent]
    def __len__(self): return len(self.contents)
    def __getitem__(self, row): return self.contents[row]


# example main window
class MainWindow(Window):
    def __init__(self):
#        print >>sys.stderr, "creating main window"
        Window.__init__(self, statusbar=True, size=(800, 600))
        self.title = 'Grafit'

        # for example
        self.main = MainPanel(self)

        self.shell = ScriptWindow(self.main.bottom_panel,
                                  page_label='console', page_pixmap='console.png')
        self.shell.locals['mainwin'] = self

        try:
            self.shell._widget.history = settings.get('script', 'history').split('\n')
        except:
            self.shell._widget.history = []
            pass
        self.explorer = ProjectExplorer(self.main.left_panel,
                                        page_label='project', page_pixmap='stock_navigator.png')
        self.actionlist = ActionList(action_list, self.main.left_panel,
                                        page_label='actions', page_pixmap='stock_undo.png')
        self.explorer.connect('item-activated', self.on_item_activated)

        self.project = Project()
        self.open_project(self.project)

        self.book = Notebook(self.main)
#        self.book.connect('page-changed', self.on_page_changed)

        self.main.left_panel.open(self.explorer)

        global_connect('status-message', self.on_status_message)
        action_list.connect('added', self.on_action)
        action_list.connect('removed', self.on_action)
        action_list.connect('modified', self.on_action)

        self.actions = actions = {
            'file-new': Command('New', 'Create a new project', self.on_project_new, 'new.png', 'Ctrl+N'),
            'file-open': Command('Open...', 'Open a project', self.on_project_open, 'open.png', 'Ctrl+O'),
            'file-save': Command('Save', 'Save the project', 
                                self.on_project_save, 'save.png', 'Ctrl+S'),
            'file-saveas': Command('Save As...', 'Save the project with a new name', 
                                  self.on_project_saveas, 'saveas.png'),
            'file-quit': Command('Quit', 'Quit grafity', self.on_quit, 'stock_exit.png', 'Ctrl+Q'),

            'edit-undo': Command('Undo', 'Undo the last action', undo, 'stock_undo.png', 'Ctrl+Z'),
            'edit-redo': Command('Redo', 'Redo the last action', redo, 'stock_redo.png', 'Shift+Ctrl+Z'),
            'edit-copy': Command('Copy', 'Undo the last action', object, 'stock_copy.png', 'Ctrl+C'),
            'edit-cut': Command('Cut', 'Undo the last action', object, 'stock_cut.png', 'Ctrl+X'),
            'edit-paste': Command('Paste', 'Undo the last action', 'stock_paste.png', None, 'Ctrl+V'),
            'edit-delete': Command('Delete', 'Undo the last action', 'stock_delete.png', None),

            'import-ascii': Command('Import ASCII...', 'Import and ASCII file', 
                                   self.on_import_ascii, 'import_ascii.png', 'Ctrl+I'),
            'object-new-worksheet': Command('New Worksheet', 'Create a new worksheet', 
                                           self.on_new_worksheet, 'new-worksheet.png'),
            'object-new-graph': Command('New Graph', 'Create a new worksheet', 
                                       self.on_new_graph, 'new-graph.png'),
            'object-new-folder': Command('New Folder', 'Create a new worksheet', 
                                        self.on_new_folder, 'new-folder.png'),
            'functions': Command('Functions...', '', object),
            'filters': Command('Filters...', '', object),
            'scripts': Command('Scripts...', '', object),
            'run-script': Command('Run script...', '', self.on_run_script),
            'integrate': Command('Integrate', '', self.on_integrate),
            'close-active-page': Command('Close', 'Close this worksheet',
                                         lambda: self.book.active_page.on_close(), 'close.png', 'Ctrl+W'),
            None: None
        }

        self.menubar = Menubar(self)
        for title, items in [
            ('&File', ['file-new', 'file-open', None, 
                       'file-save', 'file-saveas', None, 
                       'file-quit']),
            ('&Edit', ['edit-undo', 'edit-redo', None, 
                       'edit-cut', 'edit-copy', 'edit-paste', None, 'edit-delete']),
            ('&Tools', ['functions', 'filters', 'scripts', None, 'run-script']),
            ('&Analysis', ['integrate']),
            ('&Help', []),
        ]:
            menu = Menu(self.menubar, title)
            for item in items:
                menu.append(actions[item])

        self.toolbar = Toolbar(self)
        for item in [
            'file-new', 'file-open', 'file-save', 'file-saveas', None,
            'object-new-folder', 'object-new-worksheet', 'object-new-graph', None,
            'edit-undo', 'edit-redo', None,
            'import-ascii', None,
            'close-active-page',
        ]:
            self.toolbar.append(actions[item])
        self.toolbar._widget.Realize()
        
        self.connect('close', self.on_quit)

        self.main.bottom_panel._widget.toolbar.Realize()
        self.main.left_panel._widget.toolbar.Realize()
        self.main.right_panel._widget.toolbar.Realize()

        # preload
        wx.xrc.XmlResource(os.path.join(DATADIR, 'data', 'resources.xrc'))

        self.on_action()
        self.on_project_modified(False)

        if len(self.args) > 0:
            name = self.args[0]
            if ':' in name:
                prj, obj = name.split(':')
                self.open_project(Project(prj))
                self.on_item_activated(self.project.top[obj])
            else:
                self.open_project(Project(name))

    def on_integrate(self):
        page = self.book.active_page 
        if not isinstance(page, GraphView):
            return

        sys.path.append(os.path.join(DATADIR, 'data', 'scripts'))
        from integrate import integrate

        for dataset in page.graph.selected_datasets:
            w = dataset.worksheet
            ind = dataset.active_data()
            x = dataset.x[ind]
            y = dataset.y[ind]
            res = integrate(x, y)
            xname = 'int_%s_%s_x' % (dataset.x.name, dataset.y.name)
            yname = 'int_%s_%s_y' % (dataset.x.name, dataset.y.name)
            w[xname], w[yname] = x, res
            page.graph.add(w[xname], w[yname])

            

    def on_action(self, *args, **kwds):
        self.actions['edit-undo'].enabled = action_list.can_undo()
        self.actions['edit-redo'].enabled = action_list.can_redo()

    def on_status_message(self, obj, msg, time=0):
        self.status = msg

    def on_import_ascii(self):
        dlg = wx.FileDialog(self._widget, message="Choose a file", defaultDir=os.getcwd(), 
                            defaultFile="", wildcard="All Files|*.*|Projects|*.gt", style=wx.OPEN | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            ws = self.project.new(Worksheet, None, self.project.here)
            path = dlg.GetPaths()[0]
            ws.array, ws._header = import_ascii(path)
        dlg.Destroy()

    def on_project_modified(self, isit):
        self.actions['file-save'].enabled = isit

    def open_project(self, project):
        self.project = project
        for panel in (self.shell, self.explorer):
            panel.connect_project(self.project)
        self.project.connect('remove-item', self.on_project_remove_item)
        self.project.connect('modified', lambda: self.on_project_modified(True), True)
        self.project.connect('not-modified', lambda: self.on_project_modified(False), True)
#        action_list.clear()

    def on_item_activated(self, item):
#        w = Window()
#        { Graph: GraphView, Worksheet: WorksheetView }[type(item)](w, item)
#        w.show()
#        return
        if isinstance(item, Graph):
            for view in [v for v in self.book.pages if hasattr(v, 'graph')]:
                if item == view.graph:
                    self.book.select(view)
                    view.graph.recalc = True
                    view.graph.emit('redraw')
                    return
            w = GraphView(self.book, item, page_label=item.name, page_pixmap='graph.png')
            self.book.select(w)
        elif isinstance(item, Worksheet):
            for view in [v for v in self.book.pages if hasattr(v, 'worksheet')]:
                if item == view.worksheet:
                    self.book.select(view)
                    return
            w = WorksheetView(self.book, item, page_label=item.name, page_pixmap='worksheet.png')
            self.book.select(w)

#    def on_page_changed(self, item):
#        if isinstance(item, GraphView):
#            item.graph.emit('redraw')
#        print >>sys.stderr, item


    def on_quit(self):
        settings.set('script', 'history', '\n'.join(self.shell._widget.history))
        self._widget.Destroy()

    def close_project(self):
        for panel in (self.shell, self.explorer):
            panel.disconnect_project()
        for page in list(self.book.pages):
            self.book.delete(page)
        self.project.disconnect('remove-item', self.on_project_remove_item)

    def on_project_remove_item(self, item):
        for page in self.book.pages:
            if page.object == item:
                page.on_close()

    def act(self, x, y):
        print 'patataki'

    def on_new_worksheet(self):
        ws = self.project.new(Worksheet, None, self.project.here)
        ws.a = [nan]*100
        ws.b = [nan]*100

    def on_run_script(self):
        try:
            dlg = wx.FileDialog(self._widget, message="Choose a file", defaultDir=os.getcwd(), 
                                defaultFile="", wildcard="Python source files|*.py|All files|*.*", 
                                style=wx.OPEN | wx.CHANGE_DIR)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPaths()[0]
                self.shell.run('execfile("%s")' % path)
            dlg.Destroy()
        except Cancel:
            return


    def on_project_open(self):
        try:
            if self.project.modified and self.ask_savechanges():
                self.on_project_save()

            dlg = wx.FileDialog(self._widget, message="Choose a file", defaultDir=os.getcwd(), 
                                defaultFile="", wildcard="All Files|*.*|Projects|*.gt", style=wx.OPEN | wx.CHANGE_DIR)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPaths()[0]
                self.close_project()
                self.open_project(Project(str(path)))
                action_list.clear()
            dlg.Destroy()
        except Cancel:
            return

    def ask_savechanges(self):
        dlg = wx.MessageDialog(self._widget, 'Save changes to this project?', 'Save?',
                               wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            return True
        elif result == wx.ID_NO:
            return False
        elif result == wx.ID_CANCEL:
            raise Cancel
        dlg.Destroy()

    def on_project_saveas(self):
        try:
            dlg = wx.FileDialog(self._widget, message="Choose a file", defaultDir=os.getcwd(), 
                                defaultFile="", wildcard="All Files|*.*|Projects|*.mk", style=wx.SAVE | wx.CHANGE_DIR)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPaths()[0]
                self.project.saveto(path)
                self.open_project(Project(str(path)))
                action_list.clear()
            dlg.Destroy()
        except Cancel:
            return

    def on_project_save(self):
        try:
            if self.project.filename is not None:
                self.project.commit()
            else:
                self.on_project_saveas()
        except Cancel:
            return

    def on_project_new(self):
        try:
            if self.project.modified and self.ask_savechanges():
                self.on_project_save()
            self.close_project()
            self.open_project(Project())
            action_list.clear()
        except Cancel:
            return
            
    def on_new_graph(self):
        g = self.project.new(Graph, None, self.project.here)

    def on_new_folder(self):
        self.project.new(Folder, None, self.project.here)

