import os
import sys

from qt import *
from qttable import *
import qtui

from grafity.settings import settings, DATADIR
from grafity.script import Console
import grafity

pixmaps = {}
def getpixmap(name):
    if name not in pixmaps:
        pixmaps[name] = QPixmap(os.path.join(DATADIR, 'data', 'images', '16', name+'.png'))
    return pixmaps[name]

class Panel(QDockWindow):
    """A panel in the main window similar to IDEAl mode"""
    def __init__(self, mainwin, position):
        QDockWindow.__init__(self, QDockWindow.InDock, mainwin)
        self.setMovingEnabled(False)
        mainwin.moveDockWindow(self, position)
        self.position = position

        if self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
            Box1 = QVBox
            Box2 = QHBox
        elif self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
            Box1 = QHBox
            Box2 = QVBox

        self.setResizeEnabled(True)

        box = Box1(self)
        self.setWidget(box)

        if self.position in [QMainWindow.DockLeft, QMainWindow.DockTop]:
            self.buttons0 = Box2(box)

        self.stack = QWidgetStack(box)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.position in [QMainWindow.DockBottom, QMainWindow.DockRight]:
            self.buttons0 = Box2(box)

        self.buttons = Box2(self.buttons0)
        QLabel(self.buttons0)
        self.buttons.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btns = {}
        self.stack.hide()

    def add(self, name, pixmap, widget):
        if self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
            orientation = '-'
            btn = self.make_button(self.buttons, pixmap, name, '-')
        elif self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
            orientation = '|'
            btn = self.make_button(self.buttons, pixmap, name, '|')
        self.connect(btn, SIGNAL('toggled(bool)'), self.make_callback(name, widget))
        self.btns[name] = btn
        self.stack.addWidget(widget)
   
    def make_callback(self, name, widget):
        def callback(on, height=[150]):
            if on:
                for n, b in self.btns.items():
                    if n != name:
                        b.setOn(False)
                self.stack.raiseWidget(widget)
                if hasattr(widget, 'open'):
                    widget.open()
                self.stack.show()
                if height[0] is not None:
                    if self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
                        self.setFixedExtentWidth(height[0])
                    elif self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
                        self.setFixedExtentHeight(height[0])
            else:
                self.stack.hide()
                if self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
                    height[0] = self.width()
                    self.setFixedExtentWidth(0)
                elif self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
                    height[0] = self.height()
                    self.setFixedExtentHeight(0)
        setattr(self, '_%s_callback' % name, callback)
        return callback

    def make_button(self, parent, pixmap, label, orientation):
        btn2 = QPushButton(parent)
        btn2.setToggleButton(True)
        btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        pal = QPalette(btn2.palette())
        cg = QColorGroup(pal.active())
        cg.setColor(QColorGroup.Base,cg.color(QColorGroup.Background))
        bgcolor = cg.color(QColorGroup.Background)

        p = QPixmap()
        if orientation == '-':
            p.resize (90, 20)
        elif orientation == '|':
            p.resize (20, 90)
        p.fill (bgcolor)

        paint = QPainter()
        paint.begin(p)
        paint.drawPixmap (0, 0, pixmap)
        r = QRect()
        if orientation == '|':
            paint.rotate(90)
            paint.drawText (22, -2, label)
        else:
            paint.drawText (25, 15, label)
        paint.end()

        p.setMask(p.createHeuristicMask())

        btn2.setPixmap(p)

        return btn2

class ProjectExplorer(QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Expanding)
        self.setMinimumSize(QSize(150,0))
        self.setMaximumSize(QSize(150,32767))
        self.header().hide()
        self.addColumn ('Object', 145)
        self.setSelectionMode(QListView.Extended)

        self.connect (self, SIGNAL("doubleClicked(QListViewItem *, const QPoint &, int)"), self.on_doubleclick)
        self.connect (self, SIGNAL("itemRenamed (QListViewItem *, int, const QString &)"), self.on_rename)
        self.connect (self, SIGNAL("contextMenuRequested (QListViewItem *, const QPoint &, int)"),
                      self.on_context_menu_requested)

        self.wsheet_context_menu = QPopupMenu (self)
        self.wsheet_context_menu.insertItem ('Show', self.wsheet_context_menu_show)
        self.wsheet_context_menu.insertSeparator ()
        self.wsheet_context_menu.insertItem ('Delete', self.wsheet_context_menu_del)
        self.wsheet_context_menu.insertItem ('Import ASCII...', self.wsheet_context_menu_importascii)
 
        self.graph_context_menu = QPopupMenu (self)
        self.graph_context_menu.insertItem ('Show', self.graph_context_menu_show)
        self.graph_context_menu.insertSeparator ()
        self.graph_context_menu.insertItem ('Delete', self.graph_context_menu_del)
        self.graph_context_menu.insertItem ('Properties...', self.graph_context_menu_properties)
        self.graph_context_menu.insertItem ('Fit...', self.graph_context_menu_startfit)

        self.project = None

    def set_project(self, project):
        if self.project is not None:
            self.project.disconnect('add-item', self.on_add_item)
            self.project.disconnect('remove-item', self.on_remove_item)
        self.project = project
        if self.project is not None:
            self.project.connect('add-item', self.on_add_item)
            self.project.connect('remove-item', self.on_remove_item)

        project.top._tree_item = QListViewItem(self, 'top')
        project.top._tree_item.setOpen (True)
        for folder in self.project.top.all_subfolders():
            self.on_add(folder)

    def on_add_item(self, obj):
        item = obj._tree_item = QListViewItem(obj.parent._tree_item, obj.name)
        pixmap = getpixmap({grafity.Worksheet: 'worksheet', 
                            grafity.Graph: 'graph', 
                            grafity.Folder: 'folder'}[type(obj)])
        item.setPixmap (0, pixmap)
        item.setOpen (True)
        item._object = obj

    def on_remove_item(self, obj):
        obj.parent._tree_item.takeItem(obj._tree_item)
        del obj._tree_item

    def on_rename (self, item, column, text):
        if item.parent() == self.wsitem:
            item.obj.name = str(text)
        elif item.parent() == self.gritem:
            item.obj.name = str(text)

    def on_doubleclick(self, item, point, column):
        print item._object

    def dragObject(self):
        selected_worksheets = [w.name for w in project.worksheets if self.isSelected(w._explorer_item)]
        selected_graphs = [g.name for g in project.graphs if self.isSelected(g._explorer_item)]
        drag = QTextDrag('(' + ', '.join(selected_worksheets) + ' ,' + ', '.join(selected_graphs) + ')', self)
        return drag

    def on_context_menu_requested(self, item, point, column):
        if item is None:
            return
        if isinstance(item._object, grafity.Worksheet):
            self.wscontextitem = item._object
            self.wsheet_context_menu.popup(point)
        elif isinstance(item._object, grafity.Graph):
            self.grcontextitem = item._object
            self.graph_context_menu.popup(point)
            
    def graph_context_menu_show (self):
        self.grcontextitem.show()

    def graph_context_menu_del (self):
        project.remove(self.grcontextitem)

    def graph_context_menu_properties (self):
        self.grcontextitem.properties()

    def graph_context_menu_startfit (self):
        self.grcontextitem.start_fit()
 
    def wsheet_context_menu_show (self):
        v = WorksheetView (self.wscontextitem)
        v.show()
        v._table.horizontalHeader()

    def wsheet_context_menu_del (self):
        project.remove(self.wscontextitem)

    def wsheet_context_menu_importascii (self):
        # do something
        pass

import foo

class MainWindow(foo.mainwin):
    def __init__(self):
        foo.mainwin.__init__(self)

        self.mainbox = QVBox(self)
        self.setCentralWidget(self.mainbox)

        self.workspace = QWorkspace(self.mainbox)
        self.workspace.setScrollBarsEnabled(True)
        self.connect(self.workspace, SIGNAL("windowActivated(QWidget *)"), self.on_window_activated)

        self.project = grafity.Project()

        self.recent = settings.get('windows', 'recent')
        if self.recent in [None, '']:
            self.recent = []
        else:
            self.recent = [s for s in self.recent.split(' ') if os.path.isfile(s)]
        self.recentids = []

#        self.history = QListBox(self.workspace)
#        self.connect(self.history, SIGNAL("doubleClicked(QListBoxItem*)"), self.history_select)
#        self.history.setIcon(QPixmap(project.datadir + 'pixmaps/undo_history.png'))
#        self.history.setCaption('History')
#        self.history.hide()

### status bar #################################################################################

        self.statusBar().show()
        self.statusBar().message ("Welcome to Grafity", 1000)
        self.statuslabel = QLabel (self, 'Pikou')
        self.statusBar().addWidget (self.statuslabel, 0, True)
        self.statuslabel.setText ("")
        self.progressbar = QProgressBar(100, self)
        self.statusBar().addWidget (self.progressbar, 0, True)
        self.progressbar.hide()

### bottom panel ###############################################################################

        locals = {}
        locals['project'] = self.project
        locals['mainwin'] = self
        self.bpanel = Panel(self, QMainWindow.DockBottom)
        self.script = Console(self.bpanel, locals=locals)
        self.script.cmd(['from grafity import *'])

        self.bpanel.add('Script', getpixmap('console'), self.script)

### left panel #################################################################################
        self.lpanel = Panel(self, QMainWindow.DockLeft)
        self.explorer = ProjectExplorer(self.lpanel)
        self.lpanel.add('Explorer', getpixmap('folder'), self.explorer)

        self.explorer.set_project(self.project)

    def on_new_folder(self):
        self.project.new(grafity.Folder)
        
    def on_new_worksheet(self):
        self.project.new(grafity.Worksheet)

    def on_new_graph(self):
        self.project.new(grafity.Graph)

    def on_btn3(self, on, height=[None]):
        if on:
            self.rpanel.stack.show()
            if height[0] is not None:
                self.rpanel.setFixedExtentWidth(height[0])
            self.rpanel.stack.raiseWidget(self.Style)
        else:
            self.rpanel.stack.hide()
            height[0] = self.rpanel.width()
            self.rpanel.setFixedExtentWidth(0)


    def on_btn2(self, on, height=[None]):
        if on:
            self.rpanel.stack.show()
            if height[0] is not None:
                self.rpanel.setFixedExtentWidth(height[0])
            self.rpanel.stack.raiseWidget(self.Data)
        else:
            self.rpanel.stack.hide()
            height[0] = self.rpanel.width()
            self.rpanel.setFixedExtentWidth(0)


    def on_btn1(self, on, height=[None]):
        if on:
            self.stack.show()
            if height[0] is not None:
                self.bpanel.setFixedExtentHeight(height[0])
        else:
            self.stack.hide()
            height[0] = self.bpanel.height()
            self.bpanel.setFixedExtentHeight(0)

    def RunScript(self):
        qfd = QFileDialog (project.mainwin)
        qfd.setMode (QFileDialog.AnyFile)
        if qfd.exec_loop() != 1:
            return False
        file = str(qfd.selectedFile())
        project.mainwin.script.fakeUser(['execfile("%s")' % file])

    def Preferences(self):
        dlg = preferences_dialog()
        dlg.exec_loop()

    def MoveColumnLeft(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            sel = aw.worksheet.selected_columns()
            aw.worksheet._view._table.clearSelection()
            for col in sel:
                aw.worksheet.move_column(col, col-1)
                aw.worksheet._view._table.selectColumn(col-1)

    def MoveColumnRight(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            sel = aw.worksheet.selected_columns()
            aw.worksheet._view._table.clearSelection()
            for col in sel:
                aw.worksheet.move_column(col, col+1)
                aw.worksheet._view._table.selectColumn(col+1)


    def insert_menu_item(self, location, callback):
        path = location.split('/')
        menu = self.menus[path[0]]

        if len(path) == 2:
            menu.insertItem(path[1], callback)
        elif len(path) == 3:
#            ids = [menu.idAt(pos) for pos in range(menu.count())]
#            names = [menu.text(id) for id in ids]
            if not hasattr(menu, 'popups'):
                menu.popups = {}
            if path[1] not in menu.popups:
                menu.popups[path[1]] = QPopupMenu()
                menu.insertItem(path[1], menu.popups[path[1]])
            menu.popups[path[1]].insertItem(path[2], callback)

    def remove_menu_item(self, location):
        path = location.split('/')
        menu = self.menus[path[0]]

        if len(path) == 2:
            ids = [menu.idAt(pos) for pos in range(menu.count())]
            names = [menu.text(id) for id in ids]
            menu.removeItem(ids[names.index(path[1])])
        elif len(path) == 3:
            submenu = menu.popups[path[1]]
            ids = [submenu.idAt(pos) for pos in range(submenu.count())]
            names = [submenu.text(id) for id in ids]
            submenu.removeItem(ids[names.index(path[2])])
            if submenu.count() == 0:
                self.remove_menu_item('/'.join(path[:2]))
        
    def fileMenuAboutToShow(self):
        return
        menu = self.menus['&File']
        for id in self.recentids:
            menu.removeItem(id)

        self.recentids = []
        for i, name in enumerate(self.recent):
            id = menu.insertItem('%d. %s' % (i, name), self.on_recent, 0, -1, 5+i)
            menu.setItemParameter(id, i)
            self.recentids.append(id)

    def on_recent(self, id):
        project.load(self.recent[id])

    def windowMenuAboutToShow(self):
        menu = self.menus['&Window']
        menu.clear()

        menu.insertSeparator()

        for i, win in enumerate(self.workspace.windowList()):
            id = menu.insertItem('&%d %s' % (i, win.caption()))
            menu.setItemParameter(id, i)
            menu.setItemChecked(id, self.workspace.activeWindow() == win)

    def on_window_activated(self, window):
        self.active = window
        toolbars = { WorksheetView : 'Worksheet',
                          GraphView : 'Graph', }
        [self.toolbars[i].hide() for i in toolbars.itervalues()]
        self.rpanel.hide()
        if window is None or not window.isVisible() or window.__class__ not in toolbars:
            return

        self.toolbars[toolbars[window.__class__]].show()

        if isinstance(window, GraphView):
            self.rpanel.show()
            self.rpanel.Style.open()
            self.rpanel.Data.open()
            self.rpanel.Axes.open()
        elif isinstance(window, WorksheetView):
            pass

    def on_add_column(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.worksheet.add_column()
 
    def on_remove_column(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            ws = aw.worksheet
            for nam in [ws.column_names[ind] for ind in ws.selected_columns()]:
                del ws[nam]
    
   
    def make_callback(self, command_class):
        def callback():
            command = command_class()
            if hasattr(command_class, 'undo'):
                project.undolist.append(command)
            command.do()
        setattr(self, command_class.__name__ + '_callback', callback)
        return callback

    def cut (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            self.clipboard = aw.cut_selected()

    def copy (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            self.clipboard = aw.copy_selected()

    def paste (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.paste_selected(self.clipboard)

    def clear (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.clear_selected()

    def delete (self):
        pass

    def history_select(self, item):
        pos = self.history.index(item)
        id = len(project.undolist) - pos - 1
        curr = project.undolist[id]

        if hasattr(curr, 'undone') and curr.undone:
            for com in project.undolist:
                if hasattr(com, 'undone') and com.undone:
                    break
            last = project.undolist.index(com)

            for com in project.undolist[last:id+1]:
                self.do_redo(com)
        else:
            for com in project.undolist[::-1]:
                if not hasattr(com, 'undone') or not com.undone:
                    break
            last = project.undolist.index(com)

            for com in project.undolist[last:id:-1]:
                self.do_undo(com)
        self.history.setCurrentItem(pos)
        
    def do_undo(self, com):
        id = len(project.undolist) - project.undolist.index(com) - 1
        self.history.changeItem(QPixmap(project.datadir + 'pixmaps/undo.png'), self.history.text(id), id)
        project.lock_undo()
        try:
            com.undo()
        finally:
            project.unlock_undo()
        com.undone = True

    def do_redo(self, com):
        id = len(project.undolist) - project.undolist.index(com) - 1
        if hasattr(com, 'pixmap') and com.pixmap is not None:
            self.history.changeItem(com.pixmap, self.history.text(id), id)
        else:
            self.history.changeItem(self.history.text(id), id)
        project.lock_undo()
        try:
            com.do()
        finally:
            project.unlock_undo()
        com.undone = False
        
    def undo (self): 
        for com in project.undolist[::-1]:
            if not hasattr(com, 'undone') or not com.undone:
                break
        if com and (not hasattr(com, 'undone') or not com.undone):
            self.do_undo(com)
        else:
            self.statusBar().message ("No more commands to undo", 1000)
        
    def redo (self):
        for com in project.undolist:
            if hasattr(com, 'undone') and com.undone:
                break
        if com and (hasattr(com, 'undone') and com.undone):
            self.do_redo(com)
        else:
            self.statusBar().message ("No more commands to redo", 1000)


    def view_history (self, show):
        if show: self.history.show ()
        else: self.history.hide ()

#    def view_notes (self, show):
#        if show: self.notes.show ()
#        else: self.notes.hide ()

    def graph_mode (self, on): 
        modes = [ 'g_arrow', 'g_zoom', 'g_range', 'g_dreader', 'g_sreader', 'g_hand' ]
        ons = [self.actions[m].isOn() for m in modes]
        if ons.count (True) != 1: return
        Graph.graph_mode = ons.index (True)
        for g in project.graphs: g.set_mode ()

    def observe_project (self, obj, **arg):
        signal =  arg['msg']
        if signal == 'add_worksheet':
            if arg['wsheet']._view is None:
                arg['wsheet']._view = WorksheetView (arg['wsheet'])
            self.explorer.add (arg['wsheet'])
        elif signal == 'add_graph':
            self.explorer.add (arg['graph'])
        elif signal == 'remove_worksheet':
            self.explorer.remove (arg['wsheet'])
            arg['wsheet']._view.close()
            arg['wsheet'].vogel()
        elif signal == 'remove_graph':
            self.explorer.remove (arg['graph'])
            arg['graph'].vogel()

    def importAscii(self):
        self.qfd = QFileDialog (self)
        self.qfd.setMode (QFileDialog.ExistingFiles)
        if self.qfd.exec_loop() == 1:
            for f in self.qfd.selectedFiles():
                w = project.new_worksheet(os.path.splitext(os.path.split(str(f))[1])[0], [])
                w.import_ascii (str(f))

    def save_if_changed (self):
        return True
        if not project.modified:
             return True
        flag = QMessageBox.information (self, "Grafit", "<b>Do you want to save the changes you made to the document?</b><p>Your changes will be lost if you don't save them", "&Save",  "&Cancel", "&Don't Save", 0, 1)
        if flag == 0:
            return self.save_project_do()
        elif flag == 1:
            return False
        elif flag == 2: 
            return True

    def closeEvent (self, event):
        self.exit()

    def exit (self):
        settings.set('windows', 'recent', ' '.join(self.recent))
        
#        s = QString()
#        st = QTextStream(s, IO_WriteOnly)
#        st << self
#        s = str(s)
#        settings.set('windows', 'toolbars', s)
#        project.settings['/grafit/console/history'] = '\n'.join(self.script.history[-20:])
        settings.set('script', 'history', '\n'.join(self.script.history[-20:]))

        
        if not self.save_if_changed ():
            return
#        project.settings.settings.sync()
        QApplication.exit(0)
        
        
    def status_message(self, msg, time = 1000):
        self.statusBar().message(msg, time)

    def about(self):
        a = AboutWindow(self)  
        a.exec_loop()

    def help(self):
        from grafit.help import HelpWidget
        h = HelpWidget(self)
        h.show()


    def open_project_do(self):
        if not project.mainwin.save_if_changed ():
            return
        qfd = QFileDialog (project.mainwin)
        if qfd.exec_loop() != 1:
            return
        project.load (str(qfd.selectedFile()))

    def save_project_do(self): 
        if project.filename is None:
            qfd = QFileDialog (project.mainwin)
            qfd.setMode (QFileDialog.AnyFile)
            if qfd.exec_loop() != 1:
                return False
            project.filename = str(qfd.selectedFile())
        return project.save (project.filename)

    def save_project_as_do(self): 
        qfd = QFileDialog (project.mainwin)
        qfd.setMode (QFileDialog.AnyFile)
        if qfd.exec_loop() != 1:
            return False
        return project.save (str(qfd.selectedFile()))

    def new_project_do(self): 
        if not project.mainwin.save_if_changed ():
            return
        project.clear ()

    def duplicate_do(self):
        aw = project.mainwin.workspace.activeWindow()
        if aw.__class__.__name__ == 'WorksheetView':
           obj = aw.worksheet
        elif aw.__class__.__name__ == 'Graph':
           obj = aw
        else:
           return
        
        elem = obj.to_element()
        new = obj.__class__()
        new.from_element(elem)
        new.name = 'another_' + obj.name
        project.add(new)
        self.obj = new


def main ():
    app = QApplication(sys.argv)
    mainwin = MainWindow()
    app.setMainWidget(mainwin)
    mainwin.show()

    app.exec_loop()
