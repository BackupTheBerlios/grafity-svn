import os
import sys
try:
    sys.modules['grafity.ui.start'].splash.message('loading main')
except:
    pass

from qt import *

from grafity.ui.utils import getimage, column_tools, graph_modes
from grafity.signals import HasSignals, global_connect
from grafity.actions import undo, redo, action_list
from grafity.ui.graph_view import GraphView, GraphStyle, GraphData, GraphAxes, GraphFit
from grafity.ui.worksheet_view import WorksheetView
from grafity.ui.script_view import ScriptView
from grafity.import_ascii import import_ascii
from grafity.ui.console import Console

from grafity.ui.forms.main import MainWindowUI

import grafity

class ListViewItem(QListViewItem):
    def __init__(self, parent, obj):
        QListViewItem.__init__(self, parent, obj.name)
        obj._tree_item = obj
        self._object = obj

        pixmap = getimage({grafity.Worksheet: 'worksheet', 
                            grafity.Graph: 'graph', 
                            grafity.Folder: 'folder',
                            grafity.Script: 'script'}[type(obj)])
        self.setPixmap (0, pixmap)

        self._object.connect('rename', self.on_object_renamed)
        self._object.connect('set-parent', self.on_object_set_parent)

        self.setRenameEnabled(0, True)

    def on_object_renamed(self, name, item):
        self.setText(0, name)

    def on_object_set_parent(self, parent):
        self.parent().takeItem(self)
        parent._tree_item.insertItem(self)
        

class Panel(QDockWindow):
    """A panel in the main window similar to IDEAl mode"""
    def __init__(self, mainwin, position):
        QDockWindow.__init__(self, QDockWindow.InDock, mainwin)
        self.setMovingEnabled(False)
        self.setVerticallyStretchable(True)
        mainwin.moveDockWindow(self, position, True, 0)
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
        p.resize (20, 20)
        
        paint = QPainter()
        paint.begin(p)
        width = paint.fontMetrics().width(label) + 30
        paint.end()

        if orientation == '-':
            p.resize (width, 20)
        elif orientation == '|':
            p.resize (20, width)

        paint.begin(p)
        p.fill (bgcolor)
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

class ActionItem(QListViewItem):
    def __init__(self, *args):
        QListViewItem.__init__(self, *args)
        self.bgcolor_done = QColor('wheat')
#        self.bgcolor_undone = QColor('white')
    def paintCell(self, p, cg, column, width, align):
        newCg = QColorGroup(cg)
        if self._object.done:
            newCg.setColor(QColorGroup.Base, self.bgcolor_done)
        QListViewItem.paintCell(self, p, newCg, column, width, align)
        
       

class ActionList(HasSignals, QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setMinimumSize(QSize(150,0))
        self.header().hide()
        self.addColumn ('Object', 145)
        self.setSelectionMode(QListView.Extended)
        self.setSorting(-1)

        QObject.connect(self, SIGNAL("doubleClicked(QListViewItem *, const QPoint &, int)"), self.on_doubleclick)
#        QObject.connect(self, SIGNAL("contextMenuRequested (QListViewItem *, const QPoint &, int)"),
#                      self.on_context_menu_requested)

        action_list.connect('added', self.on_added)
        action_list.connect('removed', self.on_removed)
        action_list.connect('done', self.on_done)
        action_list.connect('undone', self.on_undone)

    def on_added(self, action):
        action._item = ActionItem(self, str(action))
        action._item.setPixmap(0, getimage('command-undone'))
        action._item._object = action

    def on_removed(self, action):
        self.takeItem(action._item)
        del action._item

    def on_done(self, action):
        action._item.setPixmap(0, getimage('command-undone'))

    def on_undone(self, action):
        action._item.setPixmap(0, getimage('command-done'))

    def on_doubleclick(self, item, point, column):
        com = item._object
        if com.done:
            while com.done:
                undo()
        else:
            while not com.done:
                redo()


class ObjDrag(QTextDrag):
    def __init__(self, objects, widget):
        QTextDrag.__init__(self, ' '.join(obj.id for obj in objects), widget)


class ProjectExplorer(HasSignals, QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setMinimumSize(QSize(150,0))
#        self.setMaximumSize(QSize(150,32767))
        self.header().hide()
        self.addColumn ('Object', 145)
        self.setSelectionMode(QListView.Extended)

        QObject.connect(self, SIGNAL("doubleClicked(QListViewItem *, const QPoint &, int)"), self.on_doubleclick)
        QObject.connect(self, SIGNAL("itemRenamed (QListViewItem *, int, const QString &)"), self.on_rename)
        QObject.connect(self, SIGNAL("contextMenuRequested (QListViewItem *, const QPoint &, int)"),
                      self.on_context_menu_requested)

        self.project = None

        self.mousePressed = False
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

    def set_project(self, project):
        if self.project is not None:
            self.project.disconnect('add-item', self.on_add_item)
            self.project.disconnect('remove-item', self.on_remove_item)
        self.project = project
        self.clear()
        if self.project is not None:
            self.project.connect('add-item', self.on_add_item)
            self.project.connect('remove-item', self.on_remove_item)

            self.on_add_item(self.project.top, recursive=True)
            project.top._tree_item.setOpen (True)

    def on_add_item(self, obj, recursive=False):
        try:
            parent = obj.parent._tree_item
        except AttributeError:
            parent = self
        obj._tree_item = ListViewItem(parent, obj)

        if recursive and isinstance(obj, grafity.Folder):
            for child in obj:
                self.on_add_item(child, recursive=True)

    def on_remove_item(self, obj):
        obj.parent._tree_item.takeItem(obj._tree_item)
        del obj._tree_item

    def on_rename (self, item, column, text):
        item._object.name = unicode(text)

    def on_doubleclick(self, item, point, column):
        HasSignals.emit(self, 'activated', item._object)

    def dragObject(self, *args, **kwds):
        items = [i for i in self.project.items.values() 
                   if isinstance(i, (grafity.Worksheet, grafity.Graph, grafity.Folder, grafity.Script))
                      and self.isSelected(i._tree_item)]
        drag = ObjDrag(items, self)
        return drag

    def on_context_menu_rename(self):
        self.context_item._tree_item.startRename(0)

    def on_context_menu_delete(self):
        self.project.remove(self.context_item.id)

    def on_context_menu_requested(self, item, point, column):
        self.context_menu = QPopupMenu(self)
        self.context_menu.insertItem('Rename', self.on_context_menu_rename)
        self.context_menu.insertItem('Delete', self.on_context_menu_delete)
        self.context_menu.insertSeparator ()
#        self.context_menu.insertItem ('Delete', self.wsheet_context_menu_del)
#        self.context_menu.insertItem ('Import ASCII...', self.wsheet_context_menu_importascii)

        self.context_item = item._object
        self.context_menu.popup(point)
 
    def contentsDragEnterEvent(self, event):
        if not QTextDrag.canDecode(event):
            event.ignore()
            return

        self.oldCurrent = self.currentItem()

        item = self.itemAt(self.contentsToViewport(event.pos()))
        if item is not None and isinstance(item._object, grafity.Folder):
            self.dropItem = item

    def contentsDragMoveEvent(self, event):
        if not QTextDrag.canDecode(event):
            event.ignore()
            return

        item = self.itemAt(self.contentsToViewport(event.pos()))
        if item is not None and isinstance(item._object, grafity.Folder):
#            self.setSelected(item, True)
            event.accept()
            if item != self.dropItem:
                self.dropItem = item

            if event.action() == QDropEvent.Copy:
                pass
            elif event.action() == QDropEvent.Move:
                event.acceptAction()
            elif event.action() == QDropEvent.Link:
                event.acceptAction()
        else:
            event.ignore()
            self.dropItem = None

    def contentsDragLeaveEvent(self, event):
        self.dropItem = None
        self.setCurrentItem(self.oldCurrent)
        self.setSelected(self.oldCurrent, True)

    def contentsDropEvent(self, event):
        if not QTextDrag.canDecode(event):
            event.ignore()
            return

        item = self.itemAt(self.contentsToViewport(event.pos()))
        if item is not None and isinstance(item._object, grafity.Folder):
            s = QString()
            QTextDrag.decode(event, s)
            objects = [self.project.items[id] for id in unicode(s).split()]
            for o in objects:
                o.parent = item._object
            event.accept()
        else:
            event.ignore()

    def contentsMousePressEvent(self, event):
        QListView.contentsMousePressEvent(self, event)
        if event.button() == Qt.LeftButton and not self.isRenaming():
            p = self.contentsToViewport(event.pos())
            item = self.itemAt(p)
            if item:
                if ((p.x() > self.header().sectionPos(self.header().mapToIndex(0)) +
                     self.treeStepSize()*(item.depth() + int(self.rootIsDecorated())) + self.itemMargin()) or
                     (p.x() < self.header().sectionPos(self.header().mapToIndex(0)))):
                    self.presspos = QPoint(event.pos())
                    self.mousePressed = True

    def contentsMouseMoveEvent(self, event):
        if self.mousePressed and not self.isRenaming():
            length = (self.presspos-event.pos()).manhattanLength()
            if length > QApplication.startDragDistance():
                self.mousePressed = False
                item = self.itemAt(self.contentsToViewport(self.presspos))
                if item:
                    self.dragObject().drag()

    def contentsMouseReleaseEvent(self, event):
        self.mousePressed = False


class Cancel(Exception):
    pass

class MainWindow(MainWindowUI):
    def __init__(self):
        MainWindowUI.__init__(self)

        self.mainbox = QVBox(self)
        self.setCentralWidget(self.mainbox)

        self.workspace = QWorkspace(self.mainbox)
        self.workspace.setScrollBarsEnabled(True)
        self.connect(self.workspace, SIGNAL("windowActivated(QWidget *)"), self.on_window_activated)

        self.recent = grafity.settings.get('windows', 'recent')
        if self.recent in [None, '']:
            self.recent = []
        else:
            self.recent = [s for s in self.recent.split(' ') if os.path.isfile(s)]
        self.recentids = []

        self.connect(self.File, SIGNAL('aboutToShow()'), self.fileMenuAboutToShow)
        self.connect(self.Window, SIGNAL('aboutToShow()'), self.windowMenuAboutToShow)

### status bar #################################################################################

        self.statusBar().show()
        self.statusBar().message("Welcome to Grafity", 1000)
        self.statuslabel = QLabel(self, 'Pikou')
        self.statusBar().addWidget(self.statuslabel, 0, True)
        self.statuslabel.setText("")
        self.progressbar = QProgressBar(100, self)
        self.statusBar().addWidget(self.progressbar, 0, True)
        self.progressbar.hide()

### bottom panel ###############################################################################
        locals = {}
        locals['undo'] = undo
        locals['redo'] = redo
        locals['main'] = self
        self.bpanel = Panel(self, QMainWindow.DockBottom)
        self.script = Console(self.bpanel, locals=locals)
        self.script.runsource('from grafity import *')
        self.script.runsource('from grafity.arrays import *')

        self.bpanel.add('Script', getimage('console'), self.script)

### left panel #################################################################################
        self.lpanel = Panel(self, QMainWindow.DockLeft)
        self.explorer = ProjectExplorer(self.lpanel)
        self.explorer.connect('activated', self.on_activated)
        self.lpanel.add('Explorer', getimage('folder'), self.explorer)
        self.lpanel.btns['Explorer'].setOn(True)

        self.actionlist = ActionList(self.lpanel)
        self.lpanel.add('Actions', getimage('undo'), self.actionlist)


### right panel ################################################################################
        
        self.rpanel = Panel(self, QMainWindow.DockRight)
        self.graph_data = GraphData(self.bpanel, self)
        self.graph_style = GraphStyle(self.bpanel, self)
        self.graph_axes = GraphAxes(self.bpanel, self)
        self.graph_fit = GraphFit(self.bpanel, self)
        self.rpanel.add('Data', getimage('worksheet'), self.graph_data)
        self.rpanel.add('Style', getimage('style'), self.graph_style)
        self.rpanel.add('Axes', getimage('axes'), self.graph_axes)
        self.rpanel.add('fit', getimage('function'), self.graph_fit)

        self.open_project(grafity.Project())#'../test/pdms.gt'))

        global_connect('status-message', self.status_message)

        self.worksheet_toolbar.hide()
        self.graph_toolbar.hide()
        self.script_toolbar.hide()
        self.rpanel.hide()

        self.column_tool_submenus = {'': self.Column}

        for i, (name, function, image) in enumerate(column_tools):
            if '/' in name:
                path, name = name.split('/')
            else:
                path = ''

            if path not in self.column_tool_submenus:
                self.column_tool_submenus[path] = QPopupMenu()
                self.Column.insertItem(path, self.column_tool_submenus[path])
            menu = self.column_tool_submenus[path]
            
            if image is not None:
                item = menu.insertItem(QIconSet(getimage(image)), name)
            else:
                item = menu.insertItem(name)
            menu.connectItem(item, self.on_column_tool)
            menu.setItemParameter(item, i)

        self.menubar.removeItem(self.menubar.idAt(2))
        self.menubar.removeItem(self.menubar.idAt(2))
        self.menubar.removeItem(self.menubar.idAt(2))
        self.menubar.removeItem(self.menubar.idAt(2))

        self.active = None

        if len(graph_modes):
            self.act_graph_extra = QAction(self.act_graph, 'act_extra')
            self.act_graph_extra.setToggleAction(1)
            self.act_graph_extra.addTo(self.graph_toolbar)

            self.btn = btn = self.graph_toolbar.queryList('QToolButton')[-1]

            cm = QPopupMenu (self)
            self.connect(cm, SIGNAL('activated(int)'), self.on_mode_btn)
            for i, tool in enumerate(graph_modes):
                cm.insertItem(QIconSet(getimage(tool.image)), tool.name, i)
            btn.setPopup(cm)
            btn.setPopupDelay(0)

            self.on_mode_btn(0)


        self.graph_toolbar.addSeparator()
        self.graph_text.addTo(self.graph_toolbar)

    def on_mode_btn(self, i):
        self.btn.setPixmap(getimage(graph_modes[i].image))
        self.extra_mode = graph_modes[i]
        if self.btn.isOn():
            self.active.mode = self.extra_mode.name

    def on_column_tool(self, tool):
        worksheet = self.active.worksheet
        columns = [worksheet[col] for col in worksheet._view.selected_columns]
        column_tools[tool][1](worksheet, columns)
        func = column_tools[tool][1]
        print >>sys.stderr, func, func.func_globals

    def on_activated(self, obj):
        if not hasattr(obj, '_view') or obj._view is None:
            if isinstance(obj, grafity.Graph):
                obj._view = GraphView(self.workspace, self, obj)
                obj._view.show()
            elif isinstance(obj, grafity.Worksheet):
                obj._view = WorksheetView(self.workspace, self, obj)
                obj._view.show()
            elif isinstance(obj, grafity.Script):
                obj._view = ScriptView(self.workspace, self, obj)
                obj._view.show()
        else:
            obj._view.hide()
            obj._view.show()

    def open_project(self, project):
        """Connect a project to the gui"""
        self.project = project

        self.explorer.set_project(self.project)
        self.graph_data.set_project(self.project)

#        self.project.connect('change-current-folder', self.on_change_folder)
        self.script.locals['project'] = self.project
        self.script.set_current_object(self.project.top)

    def close_project(self):
        """Disconnect the current project form the gui"""
#        self.project.disconnect('change-current-folder', self.on_change_folder)
        self.explorer.set_project(None)
        self.graph_data.set_project(None)
        self.script.set_current_object(None)
        for i in self.project.items.values():
            if hasattr(i, '_view') and i._view is not None:
                i._view.close()
        self.project = None

    def on_undo(self):
        undo()
    def on_redo(self):
        redo()

    def ask_save(self):
        """Prepare to close the project. Ask the user whether to
        save changes and save is necessary. Raises Cancel if
        the user cancels.
        """
        if not self.project.modified:
            return
        message = "<b>Do you want to save the changes you made to the document?</b>" \
                  "<p>Your changes will be lost if you don't save them"
        resp = QMessageBox.information(None, "Grafity", message, 
                                       "&Save",  "&Cancel", "&Don't Save", 0, 1)
        if resp == 0:
            self.on_project_save()
        if resp == 1:
            raise Cancel
        elif resp == 2:
            pass

    # Menu and toolbar actions

    def on_graph_mode(self):
        modes = ['arrow', 'hand', 'zoom', 'range', 'dreader', 'sreader', 'extra']
        m = modes[[getattr(self, 'act_graph_%s'%a).isOn() for a in modes].index(True)]
        if m == 'extra':
            m = self.extra_mode.name
        self.active.mode = m

    def on_project_open(self):
        """File/Open"""
        try:
            self.ask_save()
        except Cancel:
            return

        filesel = QFileDialog(self)
        if filesel.exec_loop() != 1:
            return

        filename = unicode(filesel.selectedFile())

        if filename in self.recent:
            self.recent.remove(filename)
        self.recent = ([filename]+self.recent)[:5]

        self.close_project()
        self.open_project(grafity.Project(filename))

    def on_project_save(self):
        if self.project.filename is not None:
            self.project.commit()
        else:
            self.on_project_saveas()

    def on_project_saveas(self):
        filesel = QFileDialog(self)
        filesel.setMode(QFileDialog.AnyFile)
        if filesel.exec_loop() != 1:
            return
        self.project.saveto(str(filesel.selectedFile()))
        self.close_project()
        self.open_project(grafity.Project(str(filesel.selectedFile())))

    def on_project_new(self):
        try:
            self.ask_save()
        except Cancel:
            return
        self.close_project()
        self.open_project(grafity.Project())

    def on_new_folder(self):
        self.project.new(grafity.Folder)
        
    def on_new_worksheet(self):
        self.project.new(grafity.Worksheet)

    def on_new_script(self):
        self.project.new(grafity.Script)

    def on_new_graph(self):
        self.project.new(grafity.Graph)

    def fileMenuAboutToShow(self):
        for id in self.recentids:
            self.File.removeItem(id)

        self.recentids = []
        for i, name in enumerate(self.recent):
            id = self.File.insertItem('&%d. %s' % (i, name), self.on_recent, 0, -1, 6+i)
            self.File.setItemParameter(id, i)
            self.recentids.append(id)

    def on_recent(self, id):
        try:
            self.ask_save()
        except Cancel:
            return
        self.close_project()
        self.open_project(grafity.Project(self.recent[id]))

    def windowMenuAboutToShow(self):
        menu = self.Window
        menu.clear()
        self.act_window_close.addTo(menu)
        self.act_window_closeall.addTo(menu)
        menu.insertSeparator()

        for i, win in enumerate(self.workspace.windowList()):
            id = menu.insertItem('&%d %s' % (i, win.caption()))
            menu.setItemParameter(id, i)
            menu.setItemChecked(id, self.workspace.activeWindow() == win)

    def on_window_activated(self, window):
        prev = self.active
        self.active = window

        if prev is not None:
            self.menubar.removeItem(self.menubar.idAt(2))
            self.menubar.removeItem(self.menubar.idAt(2))

        if window is None:
            self.graph_data.set_graph(None)
            self.graph_axes.set_graph(None)
            self.graph_style.set_graph(None)
            self.graph_fit.set_graph(None)

        self.worksheet_toolbar.hide()
        self.graph_toolbar.hide()
        self.script_toolbar.hide()
        self.rpanel.hide()

        if isinstance(window, GraphView):
            self.rpanel.show()
            self.graph_toolbar.show()
            self.graph_data.set_graph(window.graph)
            self.graph_axes.set_graph(window.graph)
            self.graph_style.set_graph(window.graph)
            self.graph_fit.set_graph(window.graph)
            getattr(self, 'act_graph_%s'%window.mode).setOn(True)
            self.menubar.insertItem('&Dataset', self.Dataset, -1, 2)
            self.menubar.insertItem('&Graph', self.Graph, -1, 2)

        elif isinstance(window, WorksheetView):
            self.worksheet_toolbar.show()
            self.menubar.insertItem('&Column', self.Column, -1, 2)
            self.menubar.insertItem('&Worksheet', self.Worksheet, -1, 2)

        elif isinstance(window, ScriptView):
            self.script_toolbar.show()
#            self.menubar.insertItem('&Script', self.Column, -1, 2)

    def clear (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.clear_selected()

    def delete (self):
        pass

    def closeEvent (self, event):
        self.exit()

    def exit(self):
        grafity.settings.set('windows', 'recent', ' '.join(self.recent))
        grafity.settings.set('script', 'history', '\n'.join(self.script.history[-20:]))
        
        try:
            self.ask_save()
        except Cancel:
            return
        else:
            QApplication.exit(0)
        
    def status_message(self, obj, msg, time=1000):
        self.statusBar().message(msg, time)
        self.app.processEvents()

    def about(self):
        a = AboutWindow(self)  
        a.exec_loop()

    def help(self):
        from grafit.help import HelpWidget
        h = HelpWidget(self)
        h.show()

    def on_graph_text(self):
        self.active.on_text_clicked()

    def on_worksheet_newcolumn(self):
        self.active.on_newcolumn_clicked()
    def on_worksheet_delcolumn(self):
        self.active.on_delcolumn_clicked()
    def on_worksheet_left(self):
        self.active.on_left_clicked()
    def on_worksheet_right(self):
        self.active.on_right_clicked()
    def on_worksheet_first(self):
        self.active.on_first_clicked()
    def on_worksheet_last(self):
        self.active.on_last_clicked()

    def on_script_run(self):
        self.active.on_run()

    def on_window_close(self):
        self.active.close()

    def on_window_close_all(self):
        for win in self.workspace.windowList():
            win.close()

    def on_import_ascii(self):
        qfd = QFileDialog(self)
        qfd.setMode(QFileDialog.ExistingFiles)
        if qfd.exec_loop() == 1:
            for f in qfd.selectedFiles():
                w = self.project.new(grafity.Worksheet, os.path.splitext(os.path.split(str(f))[1])[0])
                w.array, w._header = import_ascii(str(f))

def splash_message(text):
    if __name__ == '__main__':
        splash.message (text, Qt.AlignLeft, Qt.gray)
